"""Structural MODULE_IO_SCHEMAS for the six algorithmic primitives."""

from __future__ import annotations

from alpha6d.contracts import verdict_hold, verdict_pass


_INPUT_REQUIRED = {
    "RESEARCH_CONTRACT": {"question", "purpose", "claim_ceiling", "accepted_source_classes", "proof_obligations", "stop_conditions"},
    "PRIORITY_SCORE": {"dimensions_bp", "risk_bp", "uncertainty_bp", "dependency_burden_bp", "cost_burden_bp", "confidence_bp"},
    "BATCH_ENGINE": {"jobs"},
    "STATE_MACHINE": {"from", "to", "required_evidence", "receipt_ref", "actor_scope"},
    "NBA_ENGINE": {"actions"},
}

_OUTPUT_REQUIRED = {
    "GAP_ENGINE": {"verdict", "reason_code", "gap_type", "severity_bp"},
    "RESEARCH_CONTRACT": {"verdict", "reason_code", "status", "search_allowed", "completeness_bp"},
    "PRIORITY_SCORE": {"verdict", "reason_code", "eligible", "score_bp"},
    "BATCH_ENGINE": {"verdict", "reason_code", "batch_status"},
    "STATE_MACHINE": {"verdict", "reason_code", "transition_allowed"},
    "NBA_ENGINE": {"verdict", "reason_code", "selected_action_id", "selected_score_bp"},
}


def validate_module_input(module_id: str, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if module_id == "GAP_ENGINE":
        # GAP has explicit alternate negative/unknown forms used by the contract.
        if payload.get("identity_collision") is True or payload.get("current_known") is False:
            return verdict_pass()
        required = {"importance_bp", "coverage_bp", "required_coverage_bp", "evidence_deficiency_bp", "freshness_factor_bp"}
    else:
        required = _INPUT_REQUIRED.get(module_id)
        if required is None:
            return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not required.issubset(payload):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if module_id == "PRIORITY_SCORE":
        dims = payload.get("dimensions_bp")
        if not isinstance(dims, list) or len(dims) != 6:
            return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if module_id == "BATCH_ENGINE" and not isinstance(payload.get("jobs"), list):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if module_id == "STATE_MACHINE" and (not isinstance(payload.get("from"), dict) or not isinstance(payload.get("to"), dict)):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if module_id == "NBA_ENGINE" and not isinstance(payload.get("actions"), list):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    return verdict_pass()


def validate_module_output(module_id: str, output: dict) -> dict:
    if not isinstance(output, dict):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    required = _OUTPUT_REQUIRED.get(module_id)
    if required is None or not required.issubset(output):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if output.get("verdict") not in {"PASS", "HOLD"}:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    return verdict_pass()
