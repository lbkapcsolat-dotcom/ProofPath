"""Canonical module receipts."""

from __future__ import annotations

import hashlib

from alpha6d.canonical import canonical_json_bytes, sha256_hex


def make_receipt(
    module_id: str,
    module_version: str,
    input_obj: dict,
    output_obj: dict,
    verdict: str,
    reason_code: str,
    policy_obj: dict,
    evaluated_at: str,
) -> dict:
    return {
        "receipt_schema": "ALPHA_MODULE_RECEIPT_V1",
        "module_id": module_id,
        "module_version": module_version,
        "input_digest_sha256": sha256_hex(input_obj),
        "output_digest_sha256": sha256_hex(output_obj),
        "verdict": verdict,
        "reason_code": reason_code,
        "policy_fingerprint_sha256": sha256_hex(policy_obj),
        "evaluated_at": evaluated_at,
    }


def receipt_bytes(receipt: dict) -> bytes:
    return canonical_json_bytes(receipt)


def receipt_sha256(receipt: dict) -> str:
    return hashlib.sha256(receipt_bytes(receipt)).hexdigest()
