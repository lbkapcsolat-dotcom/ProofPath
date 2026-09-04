from alpha6d.nba import calculate_nba_score, select_next_best_action


def action(action_id, size, score, safe=True, effective=True, confidence=None, origin="OPEN_GAP"):
    return {
        "action_id": action_id,
        "origin": origin,
        "hard_guard_pass": safe,
        "action_size_units": size,
        "blocker_reduction_bp": score if effective else 0,
        "evidence_gain_bp": score if effective else 0,
        "downstream_unlock_bp": score if effective else 0,
        "reversibility_bp": score if effective else 0,
        "confidence_bp": score if confidence is None else confidence,
        "information_gain_bp": score if effective else 0,
        "penalty_bp": 0,
    }


def test_nba_score_is_weighted_integer_basis_points():
    assert calculate_nba_score(action("A", 1, 6150)) == 6150


def test_nba_positive_canary_prefers_smallest_safe_effective_action():
    result = select_next_best_action({
        "actions": [
            action("ACTION_A", 1, 6150),
            action("ACTION_B", 2, 9000),
            action("ACTION_C", 1, 10000, safe=False),
        ]
    })
    assert result["verdict"] == "PASS"
    assert result["selected_action_id"] == "ACTION_A"
    assert result["selected_score_bp"] == 6150


def test_nba_negative_canary_returns_hold_when_no_safe_effective_action():
    result = select_next_best_action({
        "actions": [
            action("ACTION_A", 1, 7000, safe=False),
            action("ACTION_B", 1, 0, safe=True, effective=False),
        ]
    })
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_NO_SAFE_ACTION"
    assert result["selected_action_id"] is None


def test_nba_rejects_candidates_not_derived_from_allowed_gap_or_hold_origins():
    result = select_next_best_action({"actions": [action("INVENTED", 1, 10000, origin="ARBITRARY") ]})
    assert result["reason_code"] == "HOLD_NO_SAFE_ACTION"
    assert result["selected_action_id"] is None
