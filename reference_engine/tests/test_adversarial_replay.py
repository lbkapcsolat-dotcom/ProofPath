import json
from pathlib import Path

from alpha6d.adversarial_replay import compare_adversarial_runs, write_adversarial_run


def test_adversarial_replay_is_byte_and_sha_exact(tmp_path):
    matrix_path = Path("fixtures/adversarial_matrix.json")
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"

    meta_a = write_adversarial_run(matrix_path, run_a)
    meta_b = write_adversarial_run(matrix_path, run_b)
    comparison = compare_adversarial_runs(run_a, run_b)

    assert meta_a["verdict"] == meta_b["verdict"] == "PASS"
    assert meta_a["case_count"] == meta_b["case_count"] == 1600
    assert meta_a["report_sha256"] == meta_b["report_sha256"]
    assert comparison["byte_exact_equal"] is True
    assert comparison["sha256_equal"] is True
    assert (run_a / "report.json").read_bytes() == (run_b / "report.json").read_bytes()

    report = json.loads((run_a / "report.json").read_text(encoding="utf-8"))
    assert report["failed_case_count"] == 0
