import json
from pathlib import Path

from alpha6d.adversarial import run_adversarial_matrix


MATRIX = Path("fixtures/adversarial_matrix.json")


def test_adversarial_matrix_executes_all_six_families_and_1600_cases():
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    report = run_adversarial_matrix(matrix)
    assert report["matrix_schema"] == "ALPHA_ADVERSARIAL_INVARIANT_MATRIX_V1"
    assert report["family_count"] == 6
    assert report["case_count"] == 1600
    assert report["passed_case_count"] == 1600
    assert report["failed_case_count"] == 0
    assert report["verdict"] == "PASS"
    assert all(family["verdict"] == "PASS" for family in report["families"])
