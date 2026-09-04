from alpha6d.state_machine import evaluate_transition


def test_state_positive_canary_allows_verified_review_ready_transition():
    result = evaluate_transition({
        "from": {"lifecycle": "PROCESSED", "verification": "VERIFIED", "authority": "NON_CANONICAL"},
        "to": {"lifecycle": "REVIEW_READY", "verification": "VERIFIED", "authority": "NON_CANONICAL"},
        "required_evidence": ["evidence://proof-1"],
        "receipt_ref": "receipt://transition-1",
        "actor_scope": "ANALYZE",
    })
    assert result["verdict"] == "PASS"
    assert result["transition_allowed"] is True


def test_state_negative_canary_blocks_unverified_canonical_promotion():
    result = evaluate_transition({
        "from": {"lifecycle": "PROCESSED", "verification": "UNVERIFIED", "authority": "NON_CANONICAL"},
        "to": {"lifecycle": "REVIEW_READY", "verification": "UNVERIFIED", "authority": "CANONICAL"},
        "required_evidence": [],
        "receipt_ref": "receipt://transition-2",
        "actor_scope": "ANALYZE",
    })
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_EVIDENCE"
    assert result["transition_allowed"] is False
