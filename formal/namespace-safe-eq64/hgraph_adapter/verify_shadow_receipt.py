from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hgraph_adapter.receipt import verify_shadow_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", required=True, type=Path)
    args = parser.parse_args()

    request_path = args.package_dir / "request.json"
    verdict_path = args.package_dir / "verdict.json"
    receipt_path = args.package_dir / "receipt.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))

    receipt = verify_shadow_receipt(ROOT, request, verdict, receipt_path)
    if (
        receipt["semantic_status"] != "HOLD"
        or receipt["claim_ceiling"] != "STRUCTURAL_ONLY"
        or receipt["runtime_bind"] is not False
    ):
        raise RuntimeError("XB18_RECEIPT_CLAIM_CEILING_MISMATCH")

    print("PASS_XB18_INDEPENDENT_RECEIPT_READBACK")
    print(f"XB18_RECEIPT_PAYLOAD_SHA256={receipt['payload_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
