from alpha6d.priority import evaluate_priority


def test_priority_positive_canary_matches_fixed_point_math():
    result = evaluate_priority({
        "dimensions_bp": [8000, 7000, 9000, 6000, 7000, 9000],
        "risk_bp": 1000,
        "uncertainty_bp": 900,
        "dependency_burden_bp": 1000,
        "cost_burden_bp": 0,
        "confidence_bp": 9100,
        "max_external_cost_microunits": 0,
        "estimated_external_cost_microunits": 0,
    })
    assert result["utility_bp"] == 7750
    assert result["penalty_bp"] == 725
    assert result["score_bp"] == 6392
    assert result["eligible"] is True
    assert result["verdict"] == "PASS"


def test_priority_cost_policy_is_hard_hold_and_score_is_null():
    result = evaluate_priority({
        "dimensions_bp": [10000] * 6,
        "risk_bp": 0,
        "uncertainty_bp": 0,
        "dependency_burden_bp": 0,
        "cost_burden_bp": 0,
        "confidence_bp": 10000,
        "max_external_cost_microunits": 0,
        "estimated_external_cost_microunits": 1,
    })
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_COST"
    assert result["eligible"] is False
    assert result["score_bp"] is None
