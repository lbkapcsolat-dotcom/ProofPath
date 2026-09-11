from hgraph import TS, compute_node


@compute_node
def claim_gate(
    current_pointer_present: TS[bool],
    pointer_matches_root: TS[bool],
    requested_claim_rank: TS[int],
    evidence_level_rank: TS[int],
    independent_validation: TS[bool],
    irreversible_action: TS[bool],
    human_gate: TS[bool],
    rollback_plan: TS[bool],
) -> TS[str]:
    """Minimal fail-closed ESS control-contract canary.

    This is an isolated reference-runtime canary only. It does not perform
    canonical writes, runtime admission, production promotion, pointer
    promotion, or global binding.
    """
    if not current_pointer_present.value:
        return "HOLD:MISSING_CURRENT_POINTER"

    if not pointer_matches_root.value:
        return "HOLD:AUTHORITY_DRIFT"

    if requested_claim_rank.value > evidence_level_rank.value:
        return "HOLD:CLAIM_EXCEEDS_EVIDENCE"

    if requested_claim_rank.value >= 6 and not independent_validation.value:
        return "HOLD:PRODUCTION_OVERCLAIM"

    if irreversible_action.value and not (human_gate.value and rollback_plan.value):
        return "HOLD:IRREVERSIBLE_WITHOUT_HUMAN_GATE"

    return "PASS"
