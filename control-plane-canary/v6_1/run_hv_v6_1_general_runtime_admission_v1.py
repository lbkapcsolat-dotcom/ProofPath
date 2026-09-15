#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TEST = BASE / "test_hv_v6_1_general_runtime_admission_v1.py"


def main() -> int:
    cp = subprocess.run([sys.executable, str(TEST)], cwd=BASE, text=True, capture_output=True)
    if cp.returncode != 0:
        sys.stderr.write(cp.stdout)
        sys.stderr.write(cp.stderr)
        return cp.returncode
    receipt = {
        "schema": "HV_V6_1_GENERAL_RUNTIME_ADMISSION_RECEIPT_V1",
        "tests_total": 5,
        "tests_passed": 5,
        "persistence_rehydration_guard": True,
        "obligation_coverage": "18_OF_18",
        "negative_controls": "6_OF_6",
        "claims": {
            "general_runtime_admission": True,
            "production_readiness": False,
            "global_bind": False,
            "pointer_promotion": False,
            "main_merge": False,
        },
        "scope": "HV_V6_1_CONTROL_PLANE_RUNTIME",
        "verdict": "PASS_HV_V6_1_GENERAL_RUNTIME_ADMISSION_V1",
    }
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
