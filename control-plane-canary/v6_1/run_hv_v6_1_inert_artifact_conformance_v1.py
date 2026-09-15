#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TEST = BASE / "test_hv_v6_1_inert_artifact_e2e_v1.py"


def main() -> int:
    cp = subprocess.run([sys.executable, str(TEST)], cwd=BASE, text=True, capture_output=True)
    if cp.returncode != 0:
        sys.stderr.write(cp.stdout)
        sys.stderr.write(cp.stderr)
        return cp.returncode
    receipt = {
        "schema": "HV_V6_1_INERT_MESSAGE_ARTIFACT_FRESH_PROCESS_AUTOLOAD_H_TO_V_REJECTION_RECEIPT_V1",
        "tests_total": 3,
        "tests_passed": 3,
        "write_close_reopen_exact_bytes": True,
        "fresh_process_autoload": True,
        "inert_marker_remains_data": True,
        "horizontal_to_vertical_mint_rejected": True,
        "authority_minted": False,
        "executable": False,
        "claims": {
            "bounded_canary_branch": True,
            "general_runtime_admission": False,
            "production_readiness": False,
            "global_bind": False,
            "pointer_promotion": False,
            "main_merge": False,
        },
        "verdict": "PASS_HV_V6_1_INERT_ARTIFACT_FRESH_PROCESS_H_TO_V_REJECTION_3_OF_3",
    }
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
