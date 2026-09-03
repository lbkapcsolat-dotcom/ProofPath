from alpha6d.engine import execute_module
from alpha6d.envelope import make_object_envelope


def priority_payload():
    return {
        "dimensions_bp": [8000, 7000, 9000, 6000, 7000, 9000],
        "risk_bp": 1000,
        "uncertainty_bp": 900,
        "dependency_burden_bp": 1000,
        "cost_burden_bp": 0,
        "confidence_bp": 9100,
        "max_external_cost_microunits": 0,
        "estimated_external_cost_microunits": 0,
    }


def test_execute_module_runs_only_after_envelope_and_io_schema_pass():
    envelope = make_object_envelope(
        object_id="ENGINE_TEST_1",
        object_type="task",
        payload=priority_payload(),
        policy_obj={"max_external_cost_microunits": 0},
        evaluated_at="2026-09-01T12:00:00Z",
    )
    result = execute_module("PRIORITY_SCORE", envelope)
    assert result["verdict"] == "PASS"
    assert result["score_bp"] == 6392


def test_execute_module_fails_closed_on_bad_module_schema():
    envelope = make_object_envelope(
        object_id="ENGINE_TEST_2",
        object_type="task",
        payload={"dimensions_bp": [1, 2]},
        policy_obj={},
        evaluated_at="2026-09-01T12:00:00Z",
    )
    result = execute_module("PRIORITY_SCORE", envelope)
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_SCHEMA"


def test_execute_module_honors_read_only_authority_guard_before_module():
    envelope = make_object_envelope(
        object_id="ENGINE_TEST_3",
        object_type="task",
        payload=priority_payload(),
        policy_obj={},
        evaluated_at="2026-09-01T12:00:00Z",
    )
    envelope["constraints"]["mutation_allowed"] = True
    result = execute_module("PRIORITY_SCORE", envelope)
    assert result["reason_code"] == "HOLD_AUTHORITY"
    assert result["score_bp"] is None


def test_execute_module_runs_guard_kernel_before_priority_scoring():
    envelope = make_object_envelope(
        object_id="ENGINE_TEST_4",
        object_type="task",
        payload=priority_payload(),
        policy_obj={},
        evaluated_at="2026-09-01T12:00:00Z",
    )
    result = execute_module("PRIORITY_SCORE", envelope, guard_signals={"cost_ok": False})
    assert result["reason_code"] == "HOLD_COST"
    assert result["score_bp"] is None
