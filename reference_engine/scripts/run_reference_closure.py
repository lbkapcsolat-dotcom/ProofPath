#!/usr/bin/env python3
"""Execute two isolated ALPHA FULL 6D reference-engine canary runs and compare them."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from alpha6d.canonical import canonical_json_bytes
from alpha6d.replay import compare_runs, write_suite_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="closure output directory")
    parser.add_argument("--fixtures", default="fixtures/canaries.json")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    run_a = out / "run_a"
    run_b = out / "run_b"

    summary_a = write_suite_run(args.fixtures, run_a)
    summary_b = write_suite_run(args.fixtures, run_b)
    comparison = compare_runs(run_a, run_b)

    closure_pass = (
        summary_a["canary_count"] == 12
        and summary_a["expected_match_count"] == 12
        and summary_b["canary_count"] == 12
        and summary_b["expected_match_count"] == 12
        and comparison["byte_exact_equal"]
        and comparison["sha256_equal"]
    )
    report = {
        "engine_reference_verdict": "ENGINE_REFERENCE_PASS" if closure_pass else "HOLD_REFERENCE_CLOSURE",
        "runtime_admission": "NO",
        "production_ready": False,
        "external_mutation": False,
        "pointer_promotion": False,
        "network_required": False,
        "run_a": summary_a,
        "run_b": summary_b,
        "comparison": comparison,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "closure_report.json").write_bytes(canonical_json_bytes(report) + b"\n")

    print(report["engine_reference_verdict"])
    print(f"RUN_A_CANARIES={summary_a['expected_match_count']}/{summary_a['canary_count']}")
    print(f"RUN_B_CANARIES={summary_b['expected_match_count']}/{summary_b['canary_count']}")
    print(f"BYTE_EXACT_EQUAL={comparison['byte_exact_equal']}")
    print(f"SHA256_EQUAL={comparison['sha256_equal']}")
    print(f"OUTPUTS_SHA256={summary_a['outputs_sha256']}")
    print(f"RECEIPTS_SHA256={summary_a['receipts_sha256']}")
    print(f"MANIFEST_SHA256={summary_a['manifest_sha256']}")
    return 0 if closure_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
