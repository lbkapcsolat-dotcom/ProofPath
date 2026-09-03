"""Byte-exact replay closure for adversarial invariant matrix runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from alpha6d.adversarial import run_adversarial_matrix
from alpha6d.canonical import canonical_json_bytes


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_adversarial_run(matrix_path: str | Path, output_dir: str | Path) -> dict:
    matrix_path = Path(matrix_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    report = run_adversarial_matrix(matrix)
    report_path = output_dir / "report.json"
    report_path.write_bytes(canonical_json_bytes(report) + b"\n")
    report_sha256 = _sha256_file(report_path)
    manifest_path = output_dir / "manifest.sha256"
    manifest_path.write_text(f"{report_sha256}  report.json\n", encoding="utf-8")
    return {
        "verdict": report["verdict"],
        "case_count": report["case_count"],
        "passed_case_count": report["passed_case_count"],
        "failed_case_count": report["failed_case_count"],
        "report_sha256": report_sha256,
        "manifest_sha256": _sha256_file(manifest_path),
    }


def compare_adversarial_runs(run_a_dir: str | Path, run_b_dir: str | Path) -> dict:
    run_a = Path(run_a_dir)
    run_b = Path(run_b_dir)
    names = ("report.json", "manifest.sha256")
    byte_equal = {name: (run_a / name).read_bytes() == (run_b / name).read_bytes() for name in names}
    sha_equal = {name: _sha256_file(run_a / name) == _sha256_file(run_b / name) for name in names}
    return {
        "byte_exact_equal": all(byte_equal.values()),
        "sha256_equal": all(sha_equal.values()),
        "byte_equal_by_file": byte_equal,
        "sha256_equal_by_file": sha_equal,
    }
