"""Validated envelope-to-module execution boundary."""

from __future__ import annotations

from alpha6d.batch import evaluate_batch
from alpha6d.envelope import validate_object_envelope
from alpha6d.gap import evaluate_gap
from alpha6d.guards import evaluate_guards
from alpha6d.nba import select_next_best_action
from alpha6d.priority import evaluate_priority
from alpha6d.research import evaluate_research_contract
from alpha6d.schemas import validate_module_input, validate_module_output
from alpha6d.state_machine import evaluate_transition


_DISPATCH = {
    "GAP_ENGINE": evaluate_gap,
    "RESEARCH_CONTRACT": evaluate_research_contract,
    "PRIORITY_SCORE": evaluate_priority,
    "BATCH_ENGINE": evaluate_batch,
    "STATE_MACHINE": evaluate_transition,
    "NBA_ENGINE": select_next_best_action,
}


def _hold_shape(module_id: str, verdict: dict) -> dict:
    base = dict(verdict)
    if module_id == "GAP_ENGINE":
        base.update(gap_type=None, severity_bp=None)
    elif module_id == "RESEARCH_CONTRACT":
        base.update(status="HOLD", search_allowed=False, completeness_bp=None)
    elif module_id == "PRIORITY_SCORE":
        base.update(eligible=False, utility_bp=None, penalty_bp=None, score_bp=None)
    elif module_id == "BATCH_ENGINE":
        base.update(batch_status="HOLD_0_OF_0", required_passed=0, required_total=0)
    elif module_id == "STATE_MACHINE":
        base.update(transition_allowed=False)
    elif module_id == "NBA_ENGINE":
        base.update(selected_action_id=None, selected_score_bp=None)
    return base


def execute_module(module_id: str, envelope: dict, guard_signals: dict | None = None) -> dict:
    if module_id not in _DISPATCH:
        return _hold_shape(module_id, {
            "verdict": "HOLD",
            "reason_code": "HOLD_SCHEMA",
            "first_failed_guard": "G0_SCHEMA",
            "failed_guards": ["G0_SCHEMA"],
            "eligible_for_scoring": False,
        })

    envelope_verdict = validate_object_envelope(envelope)
    if envelope_verdict["verdict"] != "PASS":
        return _hold_shape(module_id, envelope_verdict)

    payload = envelope["payload"]
    input_verdict = validate_module_input(module_id, payload)
    if input_verdict["verdict"] != "PASS":
        return _hold_shape(module_id, input_verdict)

    signals = {
        "schema_ok": True,
        "authority_ok": True,
        "policy_ok": True,
        "evidence_ok": True,
        "contradiction_free": True,
        "dependencies_ok": True,
        "cost_ok": True,
        "freshness_ok": True,
        "preconditions_ok": True,
    }
    if guard_signals:
        signals.update(guard_signals)
    guard_verdict = evaluate_guards(signals)
    if guard_verdict["verdict"] != "PASS":
        return _hold_shape(module_id, guard_verdict)

    try:
        output = _DISPATCH[module_id](payload)
    except (TypeError, ValueError, KeyError, AttributeError):
        return _hold_shape(module_id, {
            "verdict": "HOLD",
            "reason_code": "HOLD_SCHEMA",
            "first_failed_guard": "G0_SCHEMA",
            "failed_guards": ["G0_SCHEMA"],
            "eligible_for_scoring": False,
        })
    output_verdict = validate_module_output(module_id, output)
    if output_verdict["verdict"] != "PASS":
        return _hold_shape(module_id, output_verdict)
    return output
