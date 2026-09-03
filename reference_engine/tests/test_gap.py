from alpha6d.gap import evaluate_gap


def test_gap_positive_canary_computes_4320_partial_severity():
    result = evaluate_gap({
        "importance_bp": 8000,
        "coverage_bp": 4000,
        "required_coverage_bp": 10000,
        "evidence_deficiency_bp": 9000,
        "freshness_factor_bp": 10000,
        "current_known": True,
        "bound": True,
        "contradicted": False,
    })
    assert result["gap_type"] == "PARTIAL"
    assert result["severity_bp"] == 4320
    assert result["verdict"] == "PASS"


def test_gap_identity_collision_is_hard_hold_with_no_score():
    result = evaluate_gap({"identity_collision": True})
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_IDENTITY"
    assert result["severity_bp"] is None


def test_gap_unknown_is_not_classified_as_missing():
    result = evaluate_gap({"current_known": False})
    assert result["gap_type"] == "UNKNOWN"
    assert result["gap_type"] != "MISSING"
