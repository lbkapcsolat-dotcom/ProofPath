from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any


SCHEMA_NAME = "HGRAPH_XB18_SHADOW_RECEIPT_V1"
REQUIRED = {
    "schema",
    "source_namespace",
    "target_namespace",
    "semantic_status",
    "claim_ceiling",
    "runtime_bind",
    "hgraph_version",
    "request_sha256",
    "verdict_sha256",
    "adapter_sha256",
    "receipt_builder_sha256",
    "runner_sha256",
    "verifier_sha256",
    "reference_engine_sha256",
    "requirements_sha256",
    "test_manifest_sha256",
    "payload_sha256",
}
HASH_FIELDS = {
    "request_sha256",
    "verdict_sha256",
    "adapter_sha256",
    "receipt_builder_sha256",
    "runner_sha256",
    "verifier_sha256",
    "reference_engine_sha256",
    "requirements_sha256",
    "test_manifest_sha256",
    "payload_sha256",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dependency_hashes(root: Path) -> dict[str, str]:
    return {
        "adapter_sha256": sha256_bytes((root / "hgraph_adapter" / "xb18.py").read_bytes()),
        "receipt_builder_sha256": sha256_bytes((root / "hgraph_adapter" / "receipt.py").read_bytes()),
        "runner_sha256": sha256_bytes((root / "hgraph_adapter" / "run_shadow_receipt.py").read_bytes()),
        "verifier_sha256": sha256_bytes((root / "hgraph_adapter" / "verify_shadow_receipt.py").read_bytes()),
        "reference_engine_sha256": sha256_bytes((root / "reference" / "namespace_safe_engine.py").read_bytes()),
        "requirements_sha256": sha256_bytes((root / "hgraph_adapter" / "requirements.txt").read_bytes()),
        "test_manifest_sha256": sha256_bytes((root / "hgraph_adapter" / "tests" / "test_xb18.py").read_bytes()),
    }


def _validate_receipt_shape(receipt: dict[str, Any]) -> None:
    if set(receipt) != REQUIRED:
        raise ValueError("RECEIPT_FIELDS_MISMATCH")
    if receipt["schema"] != SCHEMA_NAME:
        raise ValueError("RECEIPT_SCHEMA_INVALID")
    if receipt["runtime_bind"] is not False:
        raise ValueError("RUNTIME_BIND_MUST_REMAIN_FALSE")
    if not isinstance(receipt["hgraph_version"], str) or not receipt["hgraph_version"]:
        raise ValueError("HGRAPH_VERSION_INVALID")
    for field in HASH_FIELDS:
        value = receipt[field]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise ValueError(f"INVALID_SHA256:{field}")


def build_shadow_receipt(
    root: Path,
    request: dict[str, Any],
    verdict: dict[str, Any],
) -> dict[str, Any]:
    if verdict.get("runtime_bind") is not False:
        raise ValueError("RUNTIME_BIND_MUST_REMAIN_FALSE")

    payload = {
        "schema": SCHEMA_NAME,
        "source_namespace": request.get("source_namespace"),
        "target_namespace": request.get("target_namespace"),
        "semantic_status": verdict.get("semantic_status"),
        "claim_ceiling": verdict.get("claim_ceiling"),
        "runtime_bind": False,
        "hgraph_version": importlib.metadata.version("hgraph"),
        "request_sha256": sha256_bytes(canonical_json_bytes(request)),
        "verdict_sha256": sha256_bytes(canonical_json_bytes(verdict)),
        **_dependency_hashes(root),
    }
    receipt = dict(payload)
    receipt["payload_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    _validate_receipt_shape(receipt)
    return receipt


def write_shadow_receipt(path: Path, receipt: dict[str, Any]) -> None:
    _validate_receipt_shape(receipt)
    path.write_bytes(canonical_json_bytes(receipt) + b"\n")


def _readback_receipt(path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    _validate_receipt_shape(receipt)
    payload = dict(receipt)
    claimed = payload.pop("payload_sha256")
    actual = sha256_bytes(canonical_json_bytes(payload))
    if actual != claimed:
        raise ValueError("PAYLOAD_SHA256_MISMATCH")
    return receipt


def verify_shadow_receipt(
    root: Path,
    request: dict[str, Any],
    verdict: dict[str, Any],
    receipt_path: Path,
) -> dict[str, Any]:
    receipt = _readback_receipt(receipt_path)
    expected = {
        "request_sha256": sha256_bytes(canonical_json_bytes(request)),
        "verdict_sha256": sha256_bytes(canonical_json_bytes(verdict)),
        **_dependency_hashes(root),
    }
    for field, actual in expected.items():
        if receipt[field] != actual:
            raise ValueError(f"DEPENDENCY_SHA256_MISMATCH:{field}")
    if receipt["hgraph_version"] != importlib.metadata.version("hgraph"):
        raise ValueError("HGRAPH_VERSION_MISMATCH")
    return receipt
