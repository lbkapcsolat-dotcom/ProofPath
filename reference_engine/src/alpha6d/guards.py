"""Fail-closed hard guard kernel with fixed precedence."""

from __future__ import annotations

from alpha6d.contracts import verdict_hold, verdict_pass


_GUARDS = [
    ("schema_ok", "G0_SCHEMA", "HOLD_SCHEMA"),
    ("authority_ok", "G1_AUTHORITY", "HOLD_AUTHORITY"),
    ("policy_ok", "G2_POLICY", "HOLD_POLICY"),
    ("evidence_ok", "G3_REQUIRED_EVIDENCE", "HOLD_EVIDENCE"),
    ("contradiction_free", "G4_CONTRADICTION", "HOLD_CONTRADICTION"),
    ("dependencies_ok", "G5_DEPENDENCIES", "HOLD_DEPENDENCY"),
    ("cost_ok", "G6_COST", "HOLD_COST"),
    ("freshness_ok", "G7_FRESHNESS", "HOLD_STALE"),
    ("preconditions_ok", "G8_PRECONDITION", "HOLD_PRECONDITION"),
]


def evaluate_guards(signals: dict) -> dict:
    failed: list[tuple[str, str]] = []
    for signal_name, guard_name, reason_code in _GUARDS:
        if signals.get(signal_name) is not True:
            failed.append((guard_name, reason_code))
    if not failed:
        return verdict_pass()
    first_guard, first_reason = failed[0]
    return verdict_hold(first_reason, first_guard, [guard for guard, _ in failed])
