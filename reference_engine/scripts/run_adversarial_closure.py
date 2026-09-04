#!/usr/bin/env python3
"""Execute two isolated adversarial invariant runs and prove byte/SHA equality."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from alpha6d.adversarial_replay import compare_adversarial_runs, write_adversarial_run
from alpha6d.canonical import canonical_json_bytes


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="adversarial closure output directory")
    parser.add_argument("--matrix", default="fixtures/adversarial_matrix.json")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    run_a = out / "run_a"
    run_b = out / "run_b"

    summary_a = write_adversarial_run(args.matrix, run_a)
    summary_b = write_adversarial_run(args.matrix, run_b)
    comparison = compare_adversarial_runs(run_a, run_b)

    closure_pass = (
        summary_a["verdict"] == "PASS"
        and summary_a["case_count"] == 1600
        and summary_a["passed_case_count"] == 1600
        and summary_a["failed_case_count"] == 0
        and summary_b["verdict"] == "PASS"
        and summary_b["case_count"] == 1600
        and summary_b["passed_case_count"] == 1600
        and summary_b["failed_case_count"] == 0
        and comparison["byte_exact_equal"]
        and comparison["sha256_equal"]
    )

    report = {
        "adversarial_reference_verdict": "ADVERSARIAL_REFERENCE_PASS" if closure_pass else "HOLD_ADVERSARIAL_CLOSURE",
        "matrix_schema": "ALPHA_ADVERSARIAL_INVARIANT_MATRIX_V1",
        "invariant_families": [
            "I01_UNKNOWN_NOT_MISSING",
            "I03_HOLD_DOMINATES_SCORE",
            "I05_AUTHORITY_FAIL_CLOSED",
            "I09_STATE_TRANSITION_PROOF",
            "I08_BATCH_REQUIRED_FAIL_CLOSED",
            "I12_NBA_SMALLEST_SAFE",
        ],
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
    closure_path = out / "closure_report.json"
    closure_path.write_bytes(canonical_json_bytes(report) + b"\n")

    print(report["adversarial_reference_verdict"])
    print(f"RUN_A_CASES={summary_a['passed_case_count']}/{summary_a['case_count']}")
    print(f"RUN_B_CASES={summary_b['passed_case_count']}/{summary_b['case_count']}")
    print(f"BYTE_EXACT_EQUAL={comparison['byte_exact_equal']}")
    print(f"SHA256_EQUAL={comparison['sha256_equal']}")
    print(f"REPORT_SHA256={summary_a['report_sha256']}")
    print(f"MANIFEST_SHA256={summary_a['manifest_sha256']}")
    print(f"CLOSURE_REPORT_SHA256={_sha256_file(closure_path)}")
    return 0 if closure_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
