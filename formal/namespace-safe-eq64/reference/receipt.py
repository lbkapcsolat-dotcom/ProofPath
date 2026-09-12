from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA_NAME = "EQ64_NAMESPACE_SAFE_CANARY_RECEIPT_V1"
RUN_KIND = "NEGATIVE_CANARY"
GATE_STATUS = "PASS"
REQUIRED = {
    "schema", "run_kind", "gate_status", "source_namespace", "target_namespace",
    "permutation_count", "structural_pass", "semantic_pass", "semantic_hold",
    "semantic_deny", "unexpected_passes", "fixture_sha256", "evidence_sha256",
    "engine_sha256", "runner_sha256", "receipt_builder_sha256", "result_sha256",
    "payload_sha256", "runtime_bind",
}
HASH_FIELDS = {
    "fixture_sha256", "evidence_sha256", "engine_sha256", "runner_sha256",
    "receipt_builder_sha256", "result_sha256", "payload_sha256",
}


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_bundle(parts: list[bytes]) -> str:
    framed = b"".join(len(part).to_bytes(8, "big") + part for part in parts)
    return sha256_bytes(framed)


def write_canonical_json(path: Path, value) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def _validate_receipt_shape(receipt: dict) -> None:
    if set(receipt) != REQUIRED:
        raise ValueError("RECEIPT_FIELDS_MISMATCH")
    if receipt["schema"] != SCHEMA_NAME or receipt["run_kind"] != RUN_KIND:
        raise ValueError("RECEIPT_SCHEMA_OR_RUN_KIND_INVALID")
    if receipt["gate_status"] != GATE_STATUS:
        raise ValueError("NEGATIVE_CANARY_GATE_NOT_PASS")
    if receipt["permutation_count"] != 720:
        raise ValueError("PERMUTATION_COUNT_INVALID")
    if receipt["runtime_bind"] is not False:
        raise ValueError("RUNTIME_BIND_MUST_REMAIN_FALSE")
    if receipt["structural_pass"] != 720:
        raise ValueError("NEGATIVE_CANARY_STRUCTURAL_PASS_INVALID")
    if receipt["semantic_pass"] != 0:
        raise ValueError("NEGATIVE_CANARY_SEMANTIC_LEAKAGE")
    if receipt["semantic_hold"] != 720 or receipt["semantic_deny"] != 0:
        raise ValueError("NEGATIVE_CANARY_SEMANTIC_COUNTS_INVALID")
    if receipt["unexpected_passes"] != []:
        raise ValueError("NEGATIVE_CANARY_UNEXPECTED_PASS")
    for field in HASH_FIELDS:
        value = receipt[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"INVALID_SHA256:{field}")


def build_receipt(root: Path, source_path: Path, target_path: Path, evidence_path: Path, result_path: Path) -> dict:
    engine_path = root / "reference" / "namespace_safe_engine.py"
    runner_path = root / "reference" / "permutation_canary_720.py"
    builder_path = root / "reference" / "receipt.py"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    source = json.loads(source_path.read_text(encoding="utf-8"))
    target = json.loads(target_path.read_text(encoding="utf-8"))
    payload = {
        "schema": SCHEMA_NAME,
        "run_kind": RUN_KIND,
        "gate_status": GATE_STATUS,
        "source_namespace": source["namespace_id"],
        "target_namespace": target["namespace_id"],
        "permutation_count": result["permutation_count"],
        "structural_pass": result["structural_pass"],
        "semantic_pass": result["semantic_pass"],
        "semantic_hold": result["semantic_hold"],
        "semantic_deny": result["semantic_deny"],
        "unexpected_passes": result["semantic_pass_permutations"],
        "fixture_sha256": hash_bundle([source_path.read_bytes(), target_path.read_bytes()]),
        "evidence_sha256": sha256_bytes(evidence_path.read_bytes()),
        "engine_sha256": sha256_bytes(engine_path.read_bytes()),
        "runner_sha256": sha256_bytes(runner_path.read_bytes()),
        "receipt_builder_sha256": sha256_bytes(builder_path.read_bytes()),
        "result_sha256": sha256_bytes(result_path.read_bytes()),
        "runtime_bind": False,
    }
    receipt = dict(payload)
    receipt["payload_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    _validate_receipt_shape(receipt)
    return receipt


def write_receipt(path: Path, receipt: dict) -> None:
    _validate_receipt_shape(receipt)
    write_canonical_json(path, receipt)


def readback_receipt(path: Path) -> dict:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    _validate_receipt_shape(receipt)
    payload = dict(receipt)
    claimed = payload.pop("payload_sha256")
    actual = sha256_bytes(canonical_json_bytes(payload))
    if actual != claimed:
        raise ValueError("PAYLOAD_SHA256_MISMATCH")
    return receipt
