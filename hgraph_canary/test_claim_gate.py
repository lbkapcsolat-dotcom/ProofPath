import pytest
from hgraph.test import eval_node


def load_claim_gate():
    try:
        from hgraph_canary.claim_gate import claim_gate
    except ModuleNotFoundError as exc:
        pytest.fail(f"claim_gate implementation missing: {exc}")
    return claim_gate


def run_case(
    *,
    current_pointer_present: bool = True,
    pointer_matches_root: bool = True,
    requested_claim_rank: int = 3,
    evidence_level_rank: int = 3,
    independent_validation: bool = True,
    irreversible_action: bool = False,
    human_gate: bool = False,
    rollback_plan: bool = True,
):
    claim_gate = load_claim_gate()
    return eval_node(
        claim_gate,
        [current_pointer_present],
        [pointer_matches_root],
        [requested_claim_rank],
        [evidence_level_rank],
        [independent_validation],
        [irreversible_action],
        [human_gate],
        [rollback_plan],
        __elide__=True,
    )


def test_baseline_authoritative_case_passes():
    assert run_case() == ["PASS"]


def test_missing_current_pointer_fails_closed():
    assert run_case(current_pointer_present=False) == ["HOLD:MISSING_CURRENT_POINTER"]


def test_authority_drift_fails_closed():
    assert run_case(pointer_matches_root=False) == ["HOLD:AUTHORITY_DRIFT"]


def test_production_overclaim_fails_closed():
    assert run_case(
        requested_claim_rank=6,
        evidence_level_rank=3,
        independent_validation=False,
    ) == ["HOLD:CLAIM_EXCEEDS_EVIDENCE"]


def test_irreversible_without_human_gate_fails_closed():
    assert run_case(
        irreversible_action=True,
        human_gate=False,
        rollback_plan=False,
    ) == ["HOLD:IRREVERSIBLE_WITHOUT_HUMAN_GATE"]
