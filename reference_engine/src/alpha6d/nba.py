"""Deterministic smallest-safe-effective next-best-action selection."""

from __future__ import annotations

from alpha6d.contracts import validate_bp, verdict_hold, verdict_pass


_ALLOWED_ORIGINS = {"OPEN_GAP", "HOLD_REASON", "MISSING_DEPENDENCY", "STALE_EVIDENCE", "CONTRADICTION"}

_WEIGHTS = {
    "blocker_reduction_bp": 3000,
    "evidence_gain_bp": 2500,
    "downstream_unlock_bp": 1500,
    "reversibility_bp": 1000,
    "confidence_bp": 1000,
    "information_gain_bp": 1000,
}


def calculate_nba_score(action: dict) -> int:
    weighted = 0
    for name, weight in _WEIGHTS.items():
        weighted += weight * validate_bp(action.get(name, 0), name)
    score = weighted // 10000
    penalty = validate_bp(action.get("penalty_bp", 0), "penalty_bp")
    return max(score - penalty, 0)


def _effective(action: dict) -> bool:
    return any(action.get(name, 0) > 0 for name in (
        "blocker_reduction_bp",
        "evidence_gain_bp",
        "downstream_unlock_bp",
    ))


def select_next_best_action(case: dict) -> dict:
    actions = case.get("actions", [])
    explicit_ids = [action.get("action_id") for action in actions if isinstance(action, dict) and action.get("action_id") is not None]
    if len(explicit_ids) != len(set(explicit_ids)):
        return {
            **verdict_hold("HOLD_IDENTITY"),
            "selected_action_id": None,
            "selected_score_bp": None,
        }

    eligible = []
    for action in actions:
        if action.get("origin") not in _ALLOWED_ORIGINS:
            continue
        if action.get("hard_guard_pass") is not True:
            continue
        if not _effective(action):
            continue
        size = action.get("action_size_units")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            continue
        score = calculate_nba_score(action)
        confidence = validate_bp(action.get("confidence_bp", 0), "confidence_bp")
        eligible.append((action, size, score, confidence))

    if not eligible:
        return {
            **verdict_hold("HOLD_NO_SAFE_ACTION"),
            "selected_action_id": None,
            "selected_score_bp": None,
        }

    minimum_size = min(item[1] for item in eligible)
    smallest = [item for item in eligible if item[1] == minimum_size]
    # score desc, confidence desc, action_id lexicographically asc
    smallest.sort(key=lambda item: (-item[2], -item[3], item[0]["action_id"]))
    selected, _, score, _ = smallest[0]
    return {
        **verdict_pass(),
        "selected_action_id": selected["action_id"],
        "selected_score_bp": score,
        "selected_action_size_units": minimum_size,
    }
