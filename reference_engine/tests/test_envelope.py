from alpha6d.envelope import make_object_envelope, validate_object_envelope


def test_object_envelope_has_exact_v1_contract_and_validates():
    envelope = make_object_envelope(
        object_id="CANARY_001",
        object_type="task",
        payload={"x": 1},
        policy_obj={"max_external_cost_microunits": 0},
        evaluated_at="2026-09-01T12:00:00Z",
    )
    assert envelope["schema_version"] == "ALPHA_OBJECT_ENVELOPE_V1"
    assert envelope["authority"]["mode"] == "READ_ONLY"
    assert envelope["constraints"]["mutation_allowed"] is False
    assert validate_object_envelope(envelope)["verdict"] == "PASS"


def test_object_envelope_rejects_read_only_mutation_request():
    envelope = make_object_envelope(
        object_id="CANARY_002",
        object_type="task",
        payload={},
        policy_obj={},
        evaluated_at="2026-09-01T12:00:00Z",
    )
    envelope["constraints"]["mutation_allowed"] = True
    result = validate_object_envelope(envelope)
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_AUTHORITY"
