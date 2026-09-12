from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hgraph_adapter.receipt import verify_shadow_receipt

SUMMARY_SCHEMA = "HGRAPH_XB18_REAL_SHADOW_CANARY_SUMMARY_V1"
SUMMARY_FIELDS = {
    "schema",
    "source_namespace",
    "target_namespace",
    "structural_status",
    "semantic_status",
    "claim_ceiling",
    "reason_codes",
    "runtime_bind",
    "receipt_payload_sha256",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", required=True, type=Path)
    args = parser.parse_args()

    request_path = args.package_dir / "request.json"
    verdict_path = args.package_dir / "verdict.json"
    receipt_path = args.package_dir / "receipt.json"
    summary_path = args.package_dir / "shadow_canary_summary.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))

    receipt = verify_shadow_receipt(ROOT, request, verdict, receipt_path)
    if (
        receipt["semantic_status"] != "HOLD"
        or receipt["claim_ceiling"] != "STRUCTURAL_ONLY"
        or receipt["runtime_bind"] is not False
    ):
        raise RuntimeError("XB18_RECEIPT_CLAIM_CEILING_MISMATCH")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if set(summary) != SUMMARY_FIELDS or summary.get("schema") != SUMMARY_SCHEMA:
        raise RuntimeError("XB18_SHADOW_CANARY_SUMMARY_SCHEMA_MISMATCH")
    expected_summary = {
        "schema": SUMMARY_SCHEMA,
        "source_namespace": request["source_namespace"],
        "target_namespace": request["target_namespace"],
        "structural_status": verdict["structural_status"],
        "semantic_status": verdict["semantic_status"],
        "claim_ceiling": verdict["claim_ceiling"],
        "reason_codes": verdict["reason_codes"],
        "runtime_bind": verdict["runtime_bind"],
        "receipt_payload_sha256": receipt["payload_sha256"],
    }
    if summary != expected_summary:
        raise RuntimeError("XB18_SHADOW_CANARY_SUMMARY_CONTENT_MISMATCH")
    if (
        summary["source_namespace"] != "X_AIPRBG_6GATE_DIAGNOSTIC_V1"
        or summary["target_namespace"] != "ESS_EQ64_6D_KERNEL"
        or summary["structural_status"] != "PASS"
        or summary["semantic_status"] != "HOLD"
        or summary["claim_ceiling"] != "STRUCTURAL_ONLY"
        or summary["reason_codes"] != ["NO_AXIS_LEVEL_EVIDENCE"]
        or summary["runtime_bind"] is not False
    ):
        raise RuntimeError("XB18_REAL_SHADOW_CANARY_EXPECTATION_MISMATCH")

    print("PASS_XB18_INDEPENDENT_RECEIPT_READBACK")
    print("PASS_XB18_REAL_SHADOW_CANARY_SUMMARY")
    print(f"XB18_RECEIPT_PAYLOAD_SHA256={receipt['payload_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
