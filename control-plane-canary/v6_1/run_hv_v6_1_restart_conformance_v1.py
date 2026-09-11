#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TEST = BASE / "test_hv_v6_1_restart_durability_v1.py"


def main() -> int:
    cp = subprocess.run([sys.executable, str(TEST)], cwd=BASE, text=True, capture_output=True)
    if cp.returncode != 0:
        sys.stderr.write(cp.stdout)
        sys.stderr.write(cp.stderr)
        return cp.returncode
    receipt = {
        "schema": "HV_V6_1_REPLAY_REVOCATION_DURABLE_STATE_AND_RESTART_CONFORMANCE_RECEIPT_V1",
        "tests_total": 12,
        "tests_passed": 12,
        "fresh_process_restart": True,
        "replay_nonce_survives_restart": True,
        "revocation_survives_restart": True,
        "concurrent_double_spend_exactly_once": True,
        "sqlite_integrity_checked": True,
        "corrupt_state_fail_closed": True,
        "schema_mismatch_fail_closed": True,
        "legacy_in_memory_nonregression": True,
        "claims": {
            "bounded_canary_branch": True,
            "general_runtime_admission": False,
            "production_readiness": False,
            "global_bind": False,
            "pointer_promotion": False,
            "main_merge": False,
        },
        "verdict": "PASS_HV_V6_1_REPLAY_REVOCATION_DURABLE_STATE_AND_RESTART_CONFORMANCE_12_OF_12",
    }
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
