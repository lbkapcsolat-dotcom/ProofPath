#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Mapping
from datetime import datetime, timezone

import alpha_full_6d_local_control_plane_v6_1 as core

SCHEMA = "HV_V6_1_RUNTIME_ENFORCEMENT_V1"
PASS_VERDICT = "PASS_HV_V6_1_RUNTIME_ENFORCEMENT"


class ClaimLevel(IntEnum):
    SUPPORT = 0
    LOCAL_TEST = 1
    RUNTIME = 2
    PRODUCTION = 3
    GLOBAL = 4


@dataclass(frozen=True)
class RuntimeRequest:
    candidate_id: str
    evidence_state: str
    authority_context: Mapping[str, Any] | None
    claim_level: ClaimLevel
    requires_recovery: bool = False
    support_only: bool = False


@dataclass(frozen=True)
class RuntimeDecision:
    verdict: str
    executable: bool
    obligation: str
    reason: str
    k_state: str
    core_verdict: str = ""


@dataclass
class HVRuntimeLedger:
    claim_ceiling: ClaimLevel
    consumed_nonces: set[str] = field(default_factory=set)
    revoked_provider_statement_hashes: dict[str, int] = field(default_factory=dict)
    candidates: list[str] = field(default_factory=list)
    revocation_epoch: int = 0

    def record_candidate(self, candidate_id: str) -> None:
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("CANDIDATE_ID_REQUIRED")
        if candidate_id not in self.candidates:
            self.candidates.append(candidate_id)

    def revoke(self, authority_context: Mapping[str, Any]) -> int:
        provider = authority_context.get("provider_statement")
        digest = core.signed_record_sha256(provider)
        self.revocation_epoch += 1
        self.revoked_provider_statement_hashes[digest] = self.revocation_epoch
        return self.revocation_epoch


OBLIGATION_TO_HOOK = {
    "OBL-01": "resolve_hv_runtime: missing authority branch",
    "OBL-02": "resolve_hv_runtime: core.resolve_gate exact V validation",
    "OBL-03": "resolve_hv_runtime: current_edge_sha256 == context.input_sha256",
    "OBL-04": "resolve_hv_runtime: current_state_sha256 == context.raw_export_sha256",
    "OBL-05": "resolve_hv_runtime: current_policy_sha256 == context.policy_sha256",
    "OBL-06": "HVRuntimeLedger.consumed_nonces single-use check",
    "OBL-07": "resolve_hv_runtime: provider freshness check plus core freshness revalidation",
    "OBL-08": "HVRuntimeLedger revoked provider-statement registry",
    "OBL-09": "HVRuntimeLedger.claim_ceiling non-escalation check",
    "OBL-10": "k_from_evidence total tri-state UNKNOWN->HOLD mapping",
    "OBL-11": "HVRuntimeLedger.record_candidate before authority decision",
    "OBL-12": "resolve_hv_runtime: recovery authority external-required branch",
    "OBL-13": "resolve_hv_runtime: K=HOLD non-executable branch",
    "OBL-14": "resolve_hv_runtime: K=DENY non-executable branch",
    "OBL-15": "resolve_hv_runtime: K=PASS with absent V non-executable branch",
    "OBL-16": "resolve_hv_runtime: final PASS only after all guards plus core PASS",
    "OBL-17": "attempt_horizontal_mint_v unconditional rejection",
    "OBL-18": "support_only branch plus support_mutations all false",
}


def support_mutations() -> dict[str, bool]:
    return {
        "pointer": False,  # OBL-18
        "global": False,
        "runtime": False,
        "production": False,
    }


def k_from_evidence(evidence_state: str) -> str:
    mapping = {
        "UNKNOWN": "HOLD",
        "PROVEN_NEGATIVE": "DENY",
        "PROVEN_SUFFICIENT": "PASS",
    }
    return mapping.get(evidence_state, "HOLD")


def attempt_horizontal_mint_v(_horizontal_material: Mapping[str, Any]) -> bool:
    raise PermissionError("H_ONLY_CANNOT_MINT_V")


def _hold(obligation: str, verdict: str, reason: str, *, k_state: str = "HOLD", core_verdict: str = "") -> RuntimeDecision:
    return RuntimeDecision(
        verdict=verdict,
        executable=False,
        obligation=obligation,
        reason=reason,
        k_state=k_state,
        core_verdict=core_verdict,
    )


def _pass(obligation: str, reason: str, *, k_state: str = "PASS") -> RuntimeDecision:
    return RuntimeDecision(
        verdict=PASS_VERDICT,
        executable=True,
        obligation=obligation,
        reason=reason,
        k_state=k_state,
        core_verdict=core.PASS_VERDICT,
    )


def _provider_fresh(authority_context: Mapping[str, Any], now: datetime) -> bool:
    try:
        provider = authority_context["provider_statement"]
        body = provider["body"]
        return core._freshness(body, now) == "FRESH"
    except Exception:
        return False


def _provider_statement_hash(authority_context: Mapping[str, Any]) -> str:
    return core.signed_record_sha256(authority_context["provider_statement"])


def resolve_hv_runtime(
    request: RuntimeRequest,
    ledger: HVRuntimeLedger,
    *,
    now: datetime | None = None,
    current_edge_sha256: str,
    current_state_sha256: str,
    current_policy_sha256: str,
) -> RuntimeDecision:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return _hold("OBL-07", "HOLD_TIMEZONE_REQUIRED", "RUNTIME_TIME_MUST_BE_AWARE")

    ledger.record_candidate(request.candidate_id)
    k_state = k_from_evidence(request.evidence_state)

    if request.support_only:
        return _hold("OBL-18", "HOLD_SUPPORT_ONLY_NONACTUATING", "SUPPORT_PATH_CANNOT_ACTUATE", k_state=k_state)

    if request.authority_context is None:
        if k_state == "PASS":
            return _hold("OBL-15", "HOLD_PASS_WITHOUT_V", "K_PASS_REQUIRES_VERTICAL_AUTHORITY", k_state=k_state)
        return _hold("OBL-01", "HOLD_MISSING_V", "MISSING_VERTICAL_AUTHORITY")

    if k_state == "HOLD":
        return _hold("OBL-13", "HOLD_K_STATE", "K_HOLD_NONEXECUTABLE", k_state=k_state)
    if k_state == "DENY":
        return _hold("OBL-14", "DENY_K_STATE", "K_DENY_NONEXECUTABLE", k_state=k_state)

    context = request.authority_context
    if current_edge_sha256 != context.get("input_sha256"):
        return _hold("OBL-03", "HOLD_EDGE_BIND_MISMATCH", "EDGE_CHANGED_AFTER_APPROVAL")
    if current_state_sha256 != context.get("raw_export_sha256"):
        return _hold("OBL-04", "HOLD_STATE_BIND_MISMATCH", "STATE_CHANGED_AFTER_APPROVAL")
    if current_policy_sha256 != context.get("policy_sha256"):
        return _hold("OBL-05", "HOLD_POLICY_BIND_MISMATCH", "POLICY_CHANGED_AFTER_APPROVAL")

    if not _provider_fresh(context, now):
        return _hold("OBL-07", "HOLD_EXPIRED_V", "AUTHORITY_NOT_FRESH")

    provider_hash = _provider_statement_hash(context)
    if provider_hash in ledger.revoked_provider_statement_hashes:
        return _hold("OBL-08", "HOLD_REVOKED_V", "NEWER_REVOCATION_DOMINATES")

    if request.claim_level > ledger.claim_ceiling:
        return _hold("OBL-09", "HOLD_CLAIM_ABOVE_CEILING", "CLAIM_ESCALATION_BLOCKED")

    if request.requires_recovery:
        return _hold("OBL-12", "HOLD_RECOVERY_AUTHORITY_EXTERNAL_REQUIRED", "RUNTIME_CANNOT_DERIVE_RECOVERY_AUTHORITY")

    core_decision = core.resolve_gate(context, now=now)
    if core_decision.verdict != core.PASS_VERDICT:
        return _hold("OBL-02", "HOLD_INVALID_V", core_decision.verdict)

    nonce = context.get("nonce")
    if not isinstance(nonce, str) or not nonce:
        return _hold("OBL-02", "HOLD_INVALID_V", "NONCE_REQUIRED")
    if nonce in ledger.consumed_nonces:
        return _hold("OBL-06", "HOLD_REPLAYED_V", "NONCE_ALREADY_CONSUMED")

    ledger.consumed_nonces.add(nonce)
    return _pass("OBL-16", "ALL_RUNTIME_GUARDS_SATISFIED", k_state=k_state)


if __name__ == "__main__":
    import json
    print(json.dumps({
        "schema": SCHEMA,
        "obligations_mapped": len(OBLIGATION_TO_HOOK),
        "original_core_alone_enforces_all_18": False,
        "support_mutations": support_mutations(),
    }, sort_keys=True))
