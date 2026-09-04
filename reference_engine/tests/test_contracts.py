import pytest

from alpha6d.contracts import validate_bp, verdict_hold, verdict_pass


def test_validate_bp_accepts_integer_basis_points():
    assert validate_bp(0, "x") == 0
    assert validate_bp(10000, "x") == 10000


@pytest.mark.parametrize("value", [-1, 10001, 1.5, "5000", True])
def test_validate_bp_rejects_out_of_range_or_non_integer(value):
    with pytest.raises((TypeError, ValueError)):
        validate_bp(value, "x")


def test_verdict_pass_is_canonical_and_score_eligible():
    assert verdict_pass() == {
        "verdict": "PASS",
        "reason_code": "PASS",
        "first_failed_guard": None,
        "failed_guards": [],
        "eligible_for_scoring": True,
    }


def test_verdict_hold_is_fail_closed():
    assert verdict_hold("HOLD_COST", "G6_COST") == {
        "verdict": "HOLD",
        "reason_code": "HOLD_COST",
        "first_failed_guard": "G6_COST",
        "failed_guards": ["G6_COST"],
        "eligible_for_scoring": False,
    }
