from alpha6d.schemas import validate_module_input, validate_module_output


def test_priority_schema_accepts_valid_structural_input():
    result = validate_module_input("PRIORITY_SCORE", {
        "dimensions_bp": [1, 2, 3, 4, 5, 6],
        "risk_bp": 0,
        "uncertainty_bp": 0,
        "dependency_burden_bp": 0,
        "cost_burden_bp": 0,
        "confidence_bp": 10000,
    })
    assert result["verdict"] == "PASS"


def test_priority_schema_rejects_wrong_dimension_count():
    result = validate_module_input("PRIORITY_SCORE", {
        "dimensions_bp": [1, 2],
        "risk_bp": 0,
        "uncertainty_bp": 0,
        "dependency_burden_bp": 0,
        "cost_burden_bp": 0,
        "confidence_bp": 10000,
    })
    assert result["reason_code"] == "HOLD_SCHEMA"


def test_module_output_schema_rejects_missing_required_output_field():
    result = validate_module_output("NBA_ENGINE", {"verdict": "PASS", "reason_code": "PASS"})
    assert result["reason_code"] == "HOLD_SCHEMA"
