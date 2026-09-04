"""ALPHA_OBJECT_ENVELOPE_V1 construction and validation."""

from __future__ import annotations

import re

from alpha6d.canonical import sha256_hex
from alpha6d.contracts import validate_bp, verdict_hold, verdict_pass


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_TYPES = {"artifact", "claim", "task", "source", "candidate", "gate", "action"}
_LIFECYCLE = {"DISCOVERED", "ACQUIRED", "PROCESSED", "REVIEW_READY", "RELEASE_READY", "RELEASED"}
_VERIFICATION = {"UNVERIFIED", "PARTIAL", "VERIFIED", "CONFLICTED", "STALE", "INVALID"}
_AUTHORITY_STATE = {"NON_CANONICAL", "CANDIDATE", "CANONICAL", "SUPERSEDED"}
_REQUIRED_KEYS = {
    "schema_version", "object_id", "object_type", "scope", "authority", "state", "target",
    "evidence", "dependencies", "constraints", "confidence_bp", "policy_fingerprint_sha256",
    "lineage", "payload", "created_at", "evaluated_at",
}


def make_object_envelope(
    *,
    object_id: str,
    object_type: str,
    payload: dict,
    policy_obj: dict,
    evaluated_at: str,
    confidence_bp: int = 10000,
) -> dict:
    return {
        "schema_version": "ALPHA_OBJECT_ENVELOPE_V1",
        "object_id": object_id,
        "object_type": object_type,
        "scope": {"project": "ALPHA_FULL_6D", "branch": None, "unit": None},
        "authority": {"mode": "READ_ONLY", "actor_scope": "ANALYZE", "external_action_allowed": False},
        "state": {"lifecycle": "DISCOVERED", "verification": "UNVERIFIED", "authority": "NON_CANONICAL"},
        "target": {"requirement_ids": []},
        "evidence": [],
        "dependencies": [],
        "constraints": {
            "max_external_cost_microunits": 0,
            "mutation_allowed": False,
            "external_communication_allowed": False,
        },
        "confidence_bp": validate_bp(confidence_bp, "confidence_bp"),
        "policy_fingerprint_sha256": sha256_hex(policy_obj),
        "lineage": {"parent_ids": [], "source_object_ids": []},
        "payload": payload,
        "created_at": evaluated_at,
        "evaluated_at": evaluated_at,
    }


def validate_object_envelope(envelope: dict) -> dict:
    if not isinstance(envelope, dict) or set(envelope) != _REQUIRED_KEYS:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if envelope.get("schema_version") != "ALPHA_OBJECT_ENVELOPE_V1":
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(envelope.get("object_id"), str) or not envelope["object_id"]:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if envelope.get("object_type") not in _OBJECT_TYPES:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(envelope.get("scope"), dict) or not isinstance(envelope.get("authority"), dict):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    state = envelope.get("state")
    if not isinstance(state, dict) or state.get("lifecycle") not in _LIFECYCLE or state.get("verification") not in _VERIFICATION or state.get("authority") not in _AUTHORITY_STATE:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(envelope.get("target"), dict):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(envelope.get("evidence"), list) or not isinstance(envelope.get("dependencies"), list):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    constraints = envelope.get("constraints")
    if not isinstance(constraints, dict):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    try:
        validate_bp(envelope.get("confidence_bp"), "confidence_bp")
    except (TypeError, ValueError):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    fingerprint = envelope.get("policy_fingerprint_sha256")
    if not isinstance(fingerprint, str) or _HEX64.fullmatch(fingerprint) is None:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(envelope.get("lineage"), dict) or not isinstance(envelope.get("payload"), dict):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(envelope.get("created_at"), str) or not isinstance(envelope.get("evaluated_at"), str):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")

    authority = envelope["authority"]
    if set(authority) != {"mode", "actor_scope", "external_action_allowed"}:
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if authority.get("mode") != "READ_ONLY":
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if authority.get("actor_scope") != "ANALYZE":
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if not isinstance(authority.get("external_action_allowed"), bool):
        return verdict_hold("HOLD_SCHEMA", "G0_SCHEMA")
    if authority.get("mode") == "READ_ONLY" and constraints.get("mutation_allowed") is not False:
        return verdict_hold("HOLD_AUTHORITY", "G1_AUTHORITY")
    if authority.get("external_action_allowed") is False and constraints.get("external_communication_allowed") is not False:
        return verdict_hold("HOLD_POLICY", "G2_POLICY")
    return verdict_pass()
