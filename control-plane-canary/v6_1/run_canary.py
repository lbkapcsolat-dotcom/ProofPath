#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GATE_ID = "ESS_V6_1_REAL_REPOSITORY_CONTROL_PLANE_GITHUB_ACTIONS_CANARY_V1"
FROZEN_SOURCE_SHA256 = "19864775eeebb8a1fab2fec269ac9573a6f8463efb61244fe808c0927655ecd4"
PASS_VERDICT = "PASS_V6_1_AUTHENTICATED_CONTROL_PLANE"
EXPECTED_NEGATIVE_VERDICT = "HOLD_PROVIDER_BIND_MISMATCH"
CLAIM_CEILING = "PASS_BOUNDED_REAL_GITHUB_REPOSITORY_EXECUTION_THROUGH_V6_1_CONTROL_PLANE_ONLY"
RAW_EXPORT_CLASS = "SYNTHETIC_REFERENCE_ONLY__NOT_PROVIDER_NATIVE_CHATGPT_PROVENANCE"
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "alpha_full_6d_local_control_plane_v6_1.py"
POSITIVE = HERE / "fixtures" / "positive.json"
NEGATIVE = HERE / "fixtures" / "negative.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def verify_frozen_source() -> str:
    actual = sha256_bytes(SOURCE.read_bytes())
    if actual != FROZEN_SOURCE_SHA256:
        raise RuntimeError(f"HOLD_CONTROL_PLANE_SOURCE_IDENTITY_MISMATCH:{actual}")
    return actual


def load_engine():
    verify_frozen_source()
    spec = importlib.util.spec_from_file_location("ess_v61_frozen_engine", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("HOLD_ENGINE_IMPORT_SPEC")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_bounded_canary(*, now: datetime | None = None) -> dict[str, Any]:
    cp = load_engine()
    now = now or datetime.now(timezone.utc)
    workload_value = load_json(POSITIVE)
    workload_bytes = canonical_json_bytes(workload_value)
    negative_spec = load_json(NEGATIVE)

    synthetic_raw_export = canonical_json_bytes({
        "gate_id": GATE_ID,
        "class": RAW_EXPORT_CLASS,
        "repository": os.getenv("GITHUB_REPOSITORY", "LOCAL"),
    })
    raw_export_sha256 = sha256_bytes(synthetic_raw_export)

    positive_keys = cp.generate_role_keys()
    positive_context = cp.build_valid_context(
        role_keys=positive_keys,
        workload_bytes=workload_bytes,
        raw_export_sha256=raw_export_sha256,
        nonce="GITHUB_ACTIONS_CANARY_POSITIVE_NONCE_V1",
        now=now,
        ttl_seconds=300,
    )
    positive = cp.resolve_gate(positive_context, now=now)

    negative_keys = cp.generate_role_keys()
    negative_context = cp.build_valid_context(
        role_keys=negative_keys,
        workload_bytes=workload_bytes,
        raw_export_sha256=raw_export_sha256,
        nonce="GITHUB_ACTIONS_CANARY_NEGATIVE_NONCE_V1",
        now=now,
        ttl_seconds=300,
    )
    tampered = copy.deepcopy(negative_context)
    if negative_spec != {
        "tamper_field": "nonce",
        "tamper_value": "GITHUB_ACTIONS_CANARY_TAMPERED_NONCE_V1",
    }:
        raise RuntimeError("HOLD_NEGATIVE_FIXTURE_SCHEMA_MISMATCH")
    tampered[negative_spec["tamper_field"]] = negative_spec["tamper_value"]
    negative = cp.resolve_gate(tampered, now=now)

    if positive.verdict != PASS_VERDICT or positive.eq64_bits != "111111":
        raise RuntimeError(f"HOLD_POSITIVE_PATH:{positive.verdict}:{positive.eq64_bits}")
    if negative.verdict != EXPECTED_NEGATIVE_VERDICT:
        if negative.verdict == PASS_VERDICT:
            raise RuntimeError("FAIL_FALSE_PASS_NEGATIVE_TAMPER_ACCEPTED")
        raise RuntimeError(f"HOLD_NEGATIVE_PATH_UNEXPECTED:{negative.verdict}")

    payload: dict[str, Any] = {
        "gate_id": GATE_ID,
        "repository": os.getenv("GITHUB_REPOSITORY", "LOCAL"),
        "commit_sha": os.getenv("GITHUB_SHA", "LOCAL"),
        "github_run_id": os.getenv("GITHUB_RUN_ID", "LOCAL"),
        "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "LOCAL"),
        "workflow_ref": os.getenv("GITHUB_WORKFLOW_REF", "LOCAL"),
        "git_ref": os.getenv("GITHUB_REF", "LOCAL"),
        "control_plane_source_sha256": verify_frozen_source(),
        "positive_fixture_sha256": sha256_bytes(POSITIVE.read_bytes()),
        "positive_result": {
            "verdict": positive.verdict,
            "eq64_bits": positive.eq64_bits,
            "reason": positive.reason,
        },
        "negative_fixture_sha256": sha256_bytes(NEGATIVE.read_bytes()),
        "negative_result": {
            "verdict": negative.verdict,
            "eq64_bits": negative.eq64_bits,
            "reason": negative.reason,
        },
        "raw_export_class": RAW_EXPORT_CLASS,
        "raw_export_sha256": raw_export_sha256,
        "external_actuation": False,
        "production_write": False,
        "pointer_promotion": False,
        "new_global_bind": False,
        "zero_spend": True,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at_utc": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    payload["receipt_payload_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    return payload


def write_receipt(path: Path, receipt: dict[str, Any]) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(receipt) + b"\n"
    path.write_bytes(data)
    digest = sha256_bytes(data)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest, sidecar.name


def verify_receipt(path: Path) -> None:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "gate_id": GATE_ID,
        "control_plane_source_sha256": FROZEN_SOURCE_SHA256,
        "external_actuation": False,
        "production_write": False,
        "pointer_promotion": False,
        "new_global_bind": False,
        "zero_spend": True,
        "claim_ceiling": CLAIM_CEILING,
        "raw_export_class": RAW_EXPORT_CLASS,
    }
    for key, expected in required.items():
        if receipt.get(key) != expected:
            raise RuntimeError(f"HOLD_RECEIPT_FIELD_MISMATCH:{key}")
    if receipt.get("positive_result", {}).get("verdict") != PASS_VERDICT:
        raise RuntimeError("HOLD_RECEIPT_POSITIVE_RESULT")
    if receipt.get("positive_result", {}).get("eq64_bits") != "111111":
        raise RuntimeError("HOLD_RECEIPT_POSITIVE_EQ64")
    if receipt.get("negative_result", {}).get("verdict") != EXPECTED_NEGATIVE_VERDICT:
        raise RuntimeError("HOLD_RECEIPT_NEGATIVE_RESULT")
    payload_hash = receipt.get("receipt_payload_sha256")
    without_hash = dict(receipt)
    without_hash.pop("receipt_payload_sha256", None)
    if payload_hash != sha256_bytes(canonical_json_bytes(without_hash)):
        raise RuntimeError("FAIL_RECEIPT_PAYLOAD_HASH_MISMATCH")
    sidecar = path.with_suffix(path.suffix + ".sha256")
    expected_file_hash = sidecar.read_text(encoding="utf-8").split()[0]
    if expected_file_hash != sha256_bytes(path.read_bytes()):
        raise RuntimeError("FAIL_RECEIPT_FILE_HASH_MISMATCH")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=HERE / "out" / "ESS_V6_1_GITHUB_ACTIONS_CANARY_RECEIPT_V1.json")
    parser.add_argument("--verify-receipt", type=Path)
    args = parser.parse_args()
    if args.verify_receipt:
        verify_receipt(args.verify_receipt)
        print("PASS_RECEIPT_VERIFICATION")
        return 0
    receipt = run_bounded_canary()
    digest, sidecar_name = write_receipt(args.receipt, receipt)
    print(json.dumps({
        "verdict": "PASS_BOUNDED_REAL_REPOSITORY_CONTROL_PLANE_CANARY_LOCAL_HARNESS",
        "receipt": str(args.receipt),
        "receipt_sha256": digest,
        "sidecar": sidecar_name,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
