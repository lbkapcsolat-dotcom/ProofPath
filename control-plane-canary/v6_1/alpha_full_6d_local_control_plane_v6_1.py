#!/usr/bin/env python3
"""ALPHA FULL 6D local control plane V6.1.

This is a NEW 2026-09-10 build. It does not claim recovery or patching of
any historical artifact named V6.1.

Security invariants:
- exact context schema, no caller-supplied mutable admission state
- strict JSON and fail-closed workload policy
- role-separated Ed25519 provider / verifier / executor keys
- signed, freshness-bound provider statement
- verifier-signed provenance receipt binding provider statement, raw export,
  nonce, policy, input and verification result
- control-plane-owned non-empty canary manifest
- executor may report actual measurements only
- resolver re-executes the canonical canaries in child processes and requires
  exact set and output equality
- all bindings are revalidated at resolution time
"""
from __future__ import annotations

import base64
import hashlib
import enum
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Sequence

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

BUILD_ORIGIN = "NEW_BUILD_2026-09-10"
CLAIMS_HISTORICAL_V6_1_RECOVERY = False
SCHEMA = "ALPHA_FULL_6D_LOCAL_CONTROL_PLANE_V6_1_CONTEXT_V1"
PASS_VERDICT = "PASS_V6_1_AUTHENTICATED_CONTROL_PLANE"

ALLOWED_ACTIONS = frozenset({"deploy", "audit", "test", "read_only"})
ALLOWED_TARGETS = frozenset({"local_cluster", "isolated_sandbox"})
POLICY_DOCUMENT = {
    "schema": "ALPHA_FULL_6D_V6_1_POLICY_V1",
    "allowed_actions": sorted(ALLOWED_ACTIONS),
    "allowed_targets": sorted(ALLOWED_TARGETS),
    "strict_json": True,
    "caller_mutable_admission_state": False,
    "provider_freshness": "REQUIRED_AT_RESOLUTION",
    "canary_manifest_owner": "CONTROL_PLANE",
    "canary_set_semantics": "EXACT_NONEMPTY_EQUALITY",
    "executor_expected_values": "FORBIDDEN",
    "resolver_reexecution": "REQUIRED",
}

CANARY_INPUTS = (
    ("CANARY_INVALID_UTF8", b"not-json-\xff", 2),
    ("CANARY_DUPLICATE_KEY", b'{"action":"audit","action":"deploy","target_system":"isolated_sandbox","payload":{"x":1}}', 2),
    ("CANARY_NAN", b'{"action":"audit","target_system":"isolated_sandbox","payload":{"x":NaN}}', 2),
    ("CANARY_MISSING_FIELDS", b'{"action":"audit"}', 2),
    ("CANARY_TARGET_ESCAPE", b'{"action":"audit","target_system":"arbitrary_cloud","payload":{"x":1}}', 2),
    ("CANARY_INVALID_ACTION", b'{"action":"rm -rf","target_system":"isolated_sandbox","payload":{"x":1}}', 2),
    ("CANARY_EMPTY_PAYLOAD", b'{"action":"audit","target_system":"isolated_sandbox","payload":{}}', 2),
    ("CANARY_EXTRA_FIELD", b'{"action":"audit","target_system":"isolated_sandbox","payload":{"x":1},"extra":1}', 2),
)

CONTEXT_FIELDS = {
    "schema", "build_origin", "workload_b64", "input_sha256", "raw_export_sha256", "nonce",
    "policy_sha256", "manifest_sha256", "role_public_keys", "provider_statement",
    "provenance_receipt", "executor_receipt",
}


@dataclass(frozen=True)
class Decision:
    verdict: str
    eq64_bits: str = "000000"
    reason: str = ""


class AbstainReason(str, enum.Enum):
    EXHAUSTED_LABEL_SPACE = "EXHAUSTED_LABEL_SPACE"
    OUT_OF_DISTRIBUTION = "OUT_OF_DISTRIBUTION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    AMBIGUOUS_ADMISSIBLE_SET = "AMBIGUOUS_ADMISSIBLE_SET"


@dataclass(frozen=True)
class SemanticGateDecision:
    state: str
    reason: str
    admissible_labels: tuple[str, ...]
    rejected_labels: tuple[str, ...]
    receipt_hash: str


class MissingExclusionProofException(Exception):
    pass


class SemanticInputValidationException(Exception):
    pass


UNWORDS_RECEIPT_SCHEMA = "ESS_UNWORDS_SEMANTIC_GATE_RECEIPT_V1"


@dataclass(frozen=True)
class UnwordsSemanticGate:
    min_confidence: float = 0.80
    min_margin: float = 0.15
    ood_threshold: float = 0.90

    def __post_init__(self):
        for name, value in (
            ("min_confidence", self.min_confidence),
            ("min_margin", self.min_margin),
            ("ood_threshold", self.ood_threshold),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise SemanticInputValidationException(f"{name}:FINITE_NUMBER_REQUIRED")
            if not 0.0 <= float(value) <= 1.0:
                raise SemanticInputValidationException(f"{name}:OUT_OF_RANGE")

    def evaluate_state(
        self,
        payload_bytes: bytes,
        all_labels: set[str],
        rejected_labels_with_proofs: Mapping[str, bool],
        confidence_by_label: Mapping[str, float],
        *,
        ood_score: float,
        evidence_complete: bool,
    ) -> SemanticGateDecision:
        if not isinstance(payload_bytes, bytes):
            raise SemanticInputValidationException("PAYLOAD_BYTES_REQUIRED")
        if not isinstance(all_labels, set) or not all_labels:
            raise SemanticInputValidationException("NONEMPTY_LABEL_SET_REQUIRED")
        if any(not isinstance(label, str) or not label for label in all_labels):
            raise SemanticInputValidationException("INVALID_LABEL")
        if not isinstance(rejected_labels_with_proofs, Mapping):
            raise SemanticInputValidationException("EXCLUSION_PROOF_MAP_REQUIRED")
        if not isinstance(confidence_by_label, Mapping):
            raise SemanticInputValidationException("CONFIDENCE_MAP_REQUIRED")
        if not isinstance(evidence_complete, bool):
            raise SemanticInputValidationException("EVIDENCE_COMPLETE_BOOL_REQUIRED")
        if not isinstance(ood_score, (int, float)) or isinstance(ood_score, bool) or not math.isfinite(float(ood_score)):
            raise SemanticInputValidationException("OOD_SCORE_FINITE_REQUIRED")
        ood_score = float(ood_score)
        if not 0.0 <= ood_score <= 1.0:
            raise SemanticInputValidationException("OOD_SCORE_OUT_OF_RANGE")

        rejected_labels = set(rejected_labels_with_proofs)
        if not rejected_labels.issubset(all_labels):
            raise SemanticInputValidationException("REJECTION_OUTSIDE_ONTOLOGY")
        for label, has_proof in rejected_labels_with_proofs.items():
            if has_proof is not True:
                raise MissingExclusionProofException(f"MISSING_EXCLUSION_PROOF:{label}")

        if not set(confidence_by_label).issubset(all_labels):
            raise SemanticInputValidationException("CONFIDENCE_OUTSIDE_ONTOLOGY")
        normalized_confidence: dict[str, float] = {}
        for label in sorted(all_labels):
            raw_score = confidence_by_label.get(label, 0.0)
            if not isinstance(raw_score, (int, float)) or isinstance(raw_score, bool) or not math.isfinite(float(raw_score)):
                raise SemanticInputValidationException(f"CONFIDENCE_NOT_FINITE:{label}")
            score = float(raw_score)
            if not 0.0 <= score <= 1.0:
                raise SemanticInputValidationException(f"CONFIDENCE_OUT_OF_RANGE:{label}")
            normalized_confidence[label] = score

        admissible = all_labels - rejected_labels
        state = "ABSTAIN"
        if not admissible:
            reason = AbstainReason.EXHAUSTED_LABEL_SPACE.value
        elif not evidence_complete:
            reason = AbstainReason.INSUFFICIENT_EVIDENCE.value
        elif ood_score >= self.ood_threshold:
            reason = AbstainReason.OUT_OF_DISTRIBUTION.value
        else:
            ranked = sorted(
                ((label, normalized_confidence[label]) for label in admissible),
                key=lambda item: (-item[1], item[0]),
            )
            best_label, best_score = ranked[0]
            second_score = ranked[1][1] if len(ranked) > 1 else 0.0
            if best_score < self.min_confidence:
                reason = AbstainReason.INSUFFICIENT_EVIDENCE.value
            elif best_score - second_score < self.min_margin:
                reason = AbstainReason.AMBIGUOUS_ADMISSIBLE_SET.value
            else:
                state = "CLASSIFIED"
                reason = best_label

        receipt_body = {
            "schema": UNWORDS_RECEIPT_SCHEMA,
            "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
            "all_labels": sorted(all_labels),
            "rejected_labels": sorted(rejected_labels),
            "admissible_labels": sorted(admissible),
            "exclusion_proofs": {label: True for label in sorted(rejected_labels)},
            "confidence_by_label": normalized_confidence,
            "ood_score": ood_score,
            "evidence_complete": evidence_complete,
            "thresholds": {
                "min_confidence": float(self.min_confidence),
                "min_margin": float(self.min_margin),
                "ood_threshold": float(self.ood_threshold),
            },
            "state": state,
            "reason": reason,
        }
        receipt_hash = hashlib.sha256(canonical_json_bytes(receipt_body)).hexdigest()
        return SemanticGateDecision(
            state=state,
            reason=reason,
            admissible_labels=tuple(sorted(admissible)),
            rejected_labels=tuple(sorted(rejected_labels)),
            receipt_hash=receipt_hash,
        )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(text: str) -> bytes:
    return base64.b64decode(text, validate=True)


def strict_json_loads(data: bytes) -> Any:
    def no_duplicates(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("DUPLICATE_KEY")
            out[key] = value
        return out

    def no_constants(value: str):
        raise ValueError(f"NONSTANDARD_CONSTANT:{value}")

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicates, parse_constant=no_constants)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("STRICT_JSON_REJECT") from exc


def _policy_admits(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"action", "target_system", "payload"}
        and value.get("action") in ALLOWED_ACTIONS
        and value.get("target_system") in ALLOWED_TARGETS
        and isinstance(value.get("payload"), dict)
        and bool(value["payload"])
    )


def execute_workload_bytes(data: bytes):
    try:
        value = strict_json_loads(data)
    except ValueError:
        result = {"exit_code": 2, "result": "FAIL_CLOSED_STRICT_JSON"}
        return 2, "FAIL_CLOSED_STRICT_JSON", sha256_json(result)
    if not _policy_admits(value):
        result = {"exit_code": 2, "result": "FAIL_CLOSED_POLICY"}
        return 2, "FAIL_CLOSED_POLICY", sha256_json(result)
    canonical_input = canonical_json_bytes(value)
    result = {"exit_code": 0, "result": "SUCCESS_LOCAL_REFERENCE", "input_sha256": sha256_bytes(canonical_input)}
    return 0, "SUCCESS_LOCAL_REFERENCE", sha256_json(result)


def policy_sha256() -> str:
    return sha256_json(POLICY_DOCUMENT)


def canary_manifest():
    return [
        {"test_id": test_id, "input_sha256": sha256_bytes(data), "expected_exit_code": expected}
        for test_id, data, expected in CANARY_INPUTS
    ]


def canary_manifest_sha256() -> str:
    return sha256_json(canary_manifest())


def _public_b64(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return b64encode(raw)


def _public_from_b64(text: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(b64decode(text))


def generate_role_keys():
    out = {}
    for role in ("provider", "verifier", "executor"):
        private = Ed25519PrivateKey.generate()
        out[f"{role}_private"] = private
        out[f"{role}_public"] = private.public_key()
    return out


def sign_record(private_key: Ed25519PrivateKey, body: Mapping[str, Any]):
    body_copy = dict(body)
    signature = private_key.sign(canonical_json_bytes(body_copy))
    return {"body": body_copy, "signature_b64": b64encode(signature)}


def verify_record(public_key: Ed25519PublicKey, record: Mapping[str, Any]) -> bool:
    try:
        if not isinstance(record, Mapping) or set(record) != {"body", "signature_b64"} or not isinstance(record["body"], dict):
            return False
        public_key.verify(b64decode(record["signature_b64"]), canonical_json_bytes(record["body"]))
        return True
    except Exception:
        return False


def signed_record_sha256(record: Mapping[str, Any]) -> str:
    return sha256_json(dict(record))


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(text: str) -> datetime:
    if not isinstance(text, str) or not text:
        raise ValueError("timestamp required")
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


def _freshness(body: Mapping[str, Any], now: datetime):
    issued = _parse_time(body["issued_at"])
    expires = _parse_time(body["expires_at"])
    now = now.astimezone(timezone.utc)
    if now < issued:
        return "NOT_YET_VALID"
    if now >= expires:
        return "EXPIRED"
    if expires <= issued:
        return "INVALID"
    return "FRESH"


def _subprocess_execute(data: bytes):
    proc = subprocess.run(
        [sys.executable, __file__, "--execute-b64", b64encode(data)],
        check=False, capture_output=True, text=True, timeout=10,
    )
    if proc.returncode not in (0, 2):
        raise RuntimeError(f"executor child failed: {proc.returncode}")
    payload = json.loads(proc.stdout)
    return int(payload["exit_code"]), str(payload["label"]), str(payload["output_sha256"])


def _run_canaries_local():
    measurements = []
    for test_id, data, _expected in CANARY_INPUTS:
        exit_code, _label, output_sha = execute_workload_bytes(data)
        measurements.append({
            "test_id": test_id,
            "input_sha256": sha256_bytes(data),
            "actual_exit_code": exit_code,
            "actual_output_sha256": output_sha,
        })
    return measurements


def run_canaries():
    proc = subprocess.run(
        [sys.executable, __file__, "--run-canaries"],
        check=False, capture_output=True, text=True, timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"canary child failed: {proc.returncode}")
    payload = json.loads(proc.stdout)
    if not isinstance(payload, list):
        raise RuntimeError("canary child returned non-list")
    return payload


def sign_executor_receipt(private_key, measurements: Sequence[Mapping[str, Any]], *, nonce: str, input_sha256: str, policy_sha256: str, manifest_sha256: str):
    body = {
        "schema": "ALPHA_V6_1_EXECUTOR_RECEIPT_V1",
        "measurements": [dict(m) for m in measurements],
        "nonce": nonce,
        "input_sha256": input_sha256,
        "policy_sha256": policy_sha256,
        "manifest_sha256": manifest_sha256,
    }
    return sign_record(private_key, body)


def _validate_canary_measurements(measurements):
    if not isinstance(measurements, list) or not measurements:
        return False
    allowed = {"test_id", "input_sha256", "actual_exit_code", "actual_output_sha256"}
    observed = {}
    for item in measurements:
        if not isinstance(item, dict) or set(item) != allowed:
            return False
        test_id = item.get("test_id")
        if not isinstance(test_id, str) or test_id in observed:
            return False
        observed[test_id] = item

    manifest = {m["test_id"]: m for m in canary_manifest()}
    if set(observed) != set(manifest):
        return False

    actual_fresh = {m["test_id"]: m for m in run_canaries()}
    if set(actual_fresh) != set(manifest):
        return False

    for test_id, spec in manifest.items():
        claimed = observed[test_id]
        fresh = actual_fresh[test_id]
        if claimed["input_sha256"] != spec["input_sha256"]:
            return False
        if claimed["actual_exit_code"] != spec["expected_exit_code"]:
            return False
        if claimed != fresh:
            return False
    return True


def build_valid_context(*, role_keys, workload_bytes: bytes, raw_export_sha256: str, nonce: str, now: datetime, ttl_seconds: int = 300):
    if len(raw_export_sha256) != 64:
        raise ValueError("raw export SHA256 required")
    input_sha = sha256_bytes(workload_bytes)
    pol_sha = policy_sha256()
    man_sha = canary_manifest_sha256()
    expires = now + timedelta(seconds=ttl_seconds)

    provider_body = {
        "schema": "ALPHA_V6_1_PROVIDER_STATEMENT_V1",
        "provider_id": "LOCAL_REFERENCE_PROVIDER",
        "raw_export_sha256": raw_export_sha256,
        "nonce": nonce,
        "policy_sha256": pol_sha,
        "input_sha256": input_sha,
        "issued_at": _iso(now),
        "expires_at": _iso(expires),
    }
    provider_statement = sign_record(role_keys["provider_private"], provider_body)

    provenance_body = {
        "schema": "ALPHA_V6_1_PROVENANCE_RECEIPT_V1",
        "provider_statement_sha256": signed_record_sha256(provider_statement),
        "raw_export_sha256": raw_export_sha256,
        "verification_result": "PASS",
        "nonce": nonce,
        "policy_sha256": pol_sha,
        "input_sha256": input_sha,
        "issued_at": _iso(now),
        "expires_at": _iso(expires),
    }
    provenance_receipt = sign_record(role_keys["verifier_private"], provenance_body)

    measurements = run_canaries()
    executor_receipt = sign_executor_receipt(
        role_keys["executor_private"], measurements, nonce=nonce, input_sha256=input_sha,
        policy_sha256=pol_sha, manifest_sha256=man_sha,
    )

    return {
        "schema": SCHEMA,
        "build_origin": BUILD_ORIGIN,
        "workload_b64": b64encode(workload_bytes),
        "input_sha256": input_sha,
        "raw_export_sha256": raw_export_sha256,
        "nonce": nonce,
        "policy_sha256": pol_sha,
        "manifest_sha256": man_sha,
        "role_public_keys": {
            "provider": _public_b64(role_keys["provider_public"]),
            "verifier": _public_b64(role_keys["verifier_public"]),
            "executor": _public_b64(role_keys["executor_public"]),
        },
        "provider_statement": provider_statement,
        "provenance_receipt": provenance_receipt,
        "executor_receipt": executor_receipt,
    }


def resolve_gate(context: Mapping[str, Any], *, now: datetime | None = None) -> Decision:
    now = now or datetime.now(timezone.utc)
    try:
        if not isinstance(context, Mapping) or set(context) != CONTEXT_FIELDS:
            return Decision("HOLD_CONTEXT_SCHEMA_INVALID", reason="EXACT_CONTEXT_SCHEMA_REQUIRED")
        if context.get("schema") != SCHEMA or context.get("build_origin") != BUILD_ORIGIN:
            return Decision("HOLD_CONTEXT_SCHEMA_INVALID")
        if context.get("policy_sha256") != policy_sha256():
            return Decision("HOLD_POLICY_BIND_MISMATCH")
        if context.get("manifest_sha256") != canary_manifest_sha256():
            return Decision("HOLD_MANIFEST_BIND_MISMATCH")

        workload = b64decode(context["workload_b64"])
        if sha256_bytes(workload) != context["input_sha256"]:
            return Decision("HOLD_INPUT_BIND_MISMATCH")
        exit_code, _label, _out_sha = execute_workload_bytes(workload)
        if exit_code != 0:
            return Decision("HOLD_POLICY_VIOLATION")

        keys = context["role_public_keys"]
        if not isinstance(keys, dict) or set(keys) != {"provider", "verifier", "executor"}:
            return Decision("HOLD_ROLE_KEY_SCHEMA_INVALID")
        provider_key = _public_from_b64(keys["provider"])
        verifier_key = _public_from_b64(keys["verifier"])
        executor_key = _public_from_b64(keys["executor"])
        if len({keys["provider"], keys["verifier"], keys["executor"]}) != 3:
            return Decision("HOLD_ROLE_KEY_COLLISION")

        provider = context["provider_statement"]
        if not verify_record(provider_key, provider):
            return Decision("HOLD_PROVIDER_STATEMENT_INVALID")
        pbody = provider["body"]
        freshness = _freshness(pbody, now)
        if freshness == "NOT_YET_VALID":
            return Decision("HOLD_PROVIDER_STATEMENT_NOT_YET_VALID")
        if freshness == "EXPIRED":
            return Decision("HOLD_PROVIDER_STATEMENT_EXPIRED")
        if freshness != "FRESH":
            return Decision("HOLD_PROVIDER_STATEMENT_INVALID")
        provider_expected = {
            "raw_export_sha256": context["raw_export_sha256"], "nonce": context["nonce"],
            "policy_sha256": context["policy_sha256"], "input_sha256": context["input_sha256"],
        }
        if any(pbody.get(k) != v for k, v in provider_expected.items()):
            return Decision("HOLD_PROVIDER_BIND_MISMATCH")

        provenance = context["provenance_receipt"]
        if not verify_record(verifier_key, provenance):
            return Decision("HOLD_INVALID_PROVENANCE_RECEIPT_SIGNATURE")
        prbody = provenance["body"]
        if _freshness(prbody, now) != "FRESH":
            return Decision("HOLD_PROVENANCE_RECEIPT_STALE")
        provenance_expected = {
            "provider_statement_sha256": signed_record_sha256(provider),
            "raw_export_sha256": context["raw_export_sha256"],
            "verification_result": "PASS",
            "nonce": context["nonce"],
            "policy_sha256": context["policy_sha256"],
            "input_sha256": context["input_sha256"],
        }
        if any(prbody.get(k) != v for k, v in provenance_expected.items()):
            return Decision("HOLD_PROVENANCE_RECEIPT_MISMATCH")

        executor = context["executor_receipt"]
        if not verify_record(executor_key, executor):
            return Decision("HOLD_INVALID_EXECUTOR_SIGNATURE")
        ebody = executor["body"]
        executor_expected = {
            "nonce": context["nonce"], "input_sha256": context["input_sha256"],
            "policy_sha256": context["policy_sha256"], "manifest_sha256": context["manifest_sha256"],
        }
        if any(ebody.get(k) != v for k, v in executor_expected.items()):
            return Decision("HOLD_EXECUTOR_BIND_MISMATCH")
        if not _validate_canary_measurements(ebody.get("measurements")):
            return Decision("HOLD_CANARY_MEASUREMENT_INVALID")

        return Decision(PASS_VERDICT, "111111", "ALL_BINDINGS_REVALIDATED")
    except Exception as exc:
        return Decision("HOLD_INTERNAL_VALIDATION_ERROR", reason=type(exc).__name__)


def _cli_execute_b64(encoded: str) -> int:
    data = b64decode(encoded)
    code, label, output_sha = execute_workload_bytes(data)
    sys.stdout.write(json.dumps({"exit_code": code, "label": label, "output_sha256": output_sha}, sort_keys=True))
    return code


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--execute-b64":
        raise SystemExit(_cli_execute_b64(sys.argv[2]))
    if len(sys.argv) == 2 and sys.argv[1] == "--run-canaries":
        sys.stdout.write(json.dumps(_run_canaries_local(), sort_keys=True))
        raise SystemExit(0)
    print(json.dumps({
        "artifact": "alpha_full_6d_local_control_plane_v6_1.py",
        "build_origin": BUILD_ORIGIN,
        "claims_historical_recovery": CLAIMS_HISTORICAL_V6_1_RECOVERY,
        "policy_sha256": policy_sha256(),
        "manifest_sha256": canary_manifest_sha256(),
        "canaries": len(CANARY_INPUTS),
    }, indent=2, sort_keys=True))
