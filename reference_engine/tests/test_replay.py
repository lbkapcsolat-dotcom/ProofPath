from pathlib import Path

from alpha6d.replay import compare_runs, write_suite_run


FIXTURES = Path(__file__).parents[1] / "fixtures" / "canaries.json"


def test_two_isolated_suite_runs_are_byte_identical(tmp_path):
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    summary_a = write_suite_run(FIXTURES, run_a)
    summary_b = write_suite_run(FIXTURES, run_b)

    assert summary_a["canary_count"] == 12
    assert summary_a["expected_match_count"] == 12
    assert summary_b["expected_match_count"] == 12

    for filename in ("outputs.json", "receipts.json", "manifest.sha256"):
        assert (run_a / filename).read_bytes() == (run_b / filename).read_bytes()

    comparison = compare_runs(run_a, run_b)
    assert comparison["byte_exact_equal"] is True
    assert comparison["sha256_equal"] is True
