from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from coverage_check import validate_coverage


def test_full_spec_to_lean_coverage_bijection():
    report = validate_coverage(ROOT)
    assert report["spec_revision_bound"] is True
    assert report["source_sha_bound"] is True
    assert report["axiom_coverage"] == "12/12"
    assert report["countermodel_coverage"] == "12/12"
    assert report["derived_theorem_coverage"] == "8/8"
    assert report["primary_obligation_bijection"] == "32/32"
    assert report["countermodel_direct_bijection"] is True
    assert report["unknown_manifest_symbols"] == []
    assert report["orphan_lean_theorems"] == []
    assert report["proof_escape_declarations"] == []
    assert report["verdict"] == "PASS_RCCA_SPEC_TO_LEAN_COVERAGE_BIJECTION_AND_NO_ORPHAN_PROOF"


def test_workflow_is_persistent_main_gate():
    workflow = (ROOT / ".github/workflows/rcca-spec-lean-coverage.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "branches:\n      - main" in workflow
    assert workflow.count("- main") >= 2
    assert "formal/rcca-lean4/RCCA.lean" in workflow
    assert "formal/rcca-lean4/coverage/**" in workflow


if __name__ == "__main__":
    test_full_spec_to_lean_coverage_bijection()
    test_workflow_is_persistent_main_gate()
    print("PASS_TEST_RCCA_SPEC_TO_LEAN_COVERAGE_BIJECTION")
