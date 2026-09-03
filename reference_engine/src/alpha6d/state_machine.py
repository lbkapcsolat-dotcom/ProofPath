"""Orthogonal artifact lifecycle, verification, and authority transitions."""

from __future__ import annotations

from alpha6d.contracts import verdict_hold, verdict_pass


LIFECYCLE = ["DISCOVERED", "ACQUIRED", "PROCESSED", "REVIEW_READY", "RELEASE_READY", "RELEASED"]
VERIFICATION = {"UNVERIFIED", "PARTIAL", "VERIFIED", "CONFLICTED", "STALE", "INVALID"}
AUTHORITY = ["NON_CANONICAL", "CANDIDATE", "CANONICAL", "SUPERSEDED"]


def _valid_state(state: dict) -> bool:
    return (
        state.get("lifecycle") in LIFECYCLE
        and state.get("verification") in VERIFICATION
        and state.get("authority") in AUTHORITY
    )


def evaluate_transition(case: dict) -> dict:
    before = case.get("from", {})
    after = case.get("to", {})
    if not _valid_state(before) or not _valid_state(after):
        return {**verdict_hold("HOLD_SCHEMA", "G0_SCHEMA"), "transition_allowed": False}

    # Canonical authority can never be manufactured from unverified evidence.
    if after["authority"] == "CANONICAL" and before["verification"] != "VERIFIED":
        return {**verdict_hold("HOLD_EVIDENCE", "G3_REQUIRED_EVIDENCE"), "transition_allowed": False}
    if after["authority"] == "CANONICAL" and after["verification"] != "VERIFIED":
        return {**verdict_hold("HOLD_EVIDENCE", "G3_REQUIRED_EVIDENCE"), "transition_allowed": False}

    # Verification state changes must never manufacture or erase proof silently.
    if after["verification"] != before["verification"] and not case.get("required_evidence"):
        return {**verdict_hold("HOLD_EVIDENCE", "G3_REQUIRED_EVIDENCE"), "transition_allowed": False}

    # Authority changes require explicit promotion scope, evidence, and one-step forward motion.
    if after["authority"] != before["authority"]:
        if case.get("actor_scope") != "PROMOTE":
            return {**verdict_hold("HOLD_AUTHORITY", "G1_AUTHORITY"), "transition_allowed": False}
        if not case.get("required_evidence"):
            return {**verdict_hold("HOLD_EVIDENCE", "G3_REQUIRED_EVIDENCE"), "transition_allowed": False}
        before_auth_idx = AUTHORITY.index(before["authority"])
        after_auth_idx = AUTHORITY.index(after["authority"])
        if after_auth_idx - before_auth_idx != 1:
            return {**verdict_hold("HOLD_PRECONDITION", "G8_PRECONDITION"), "transition_allowed": False}

    # Lifecycle may remain in place or advance one step; no silent jumps/backtracking.
    before_idx = LIFECYCLE.index(before["lifecycle"])
    after_idx = LIFECYCLE.index(after["lifecycle"])
    if after_idx < before_idx or after_idx - before_idx > 1:
        return {**verdict_hold("HOLD_PRECONDITION", "G8_PRECONDITION"), "transition_allowed": False}

    if not case.get("receipt_ref"):
        return {**verdict_hold("HOLD_EVIDENCE", "G3_REQUIRED_EVIDENCE"), "transition_allowed": False}

    return {**verdict_pass(), "transition_allowed": True}
