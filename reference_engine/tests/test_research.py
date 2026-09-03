from alpha6d.research import evaluate_research_contract


def complete_case():
    return {
        "question": "What changed?",
        "purpose": "Evidence-backed decision",
        "claim_ceiling": "bounded factual claim",
        "accepted_source_classes": ["primary", "peer_reviewed"],
        "proof_obligations": ["source_identity", "freshness"],
        "stop_conditions": ["all obligations satisfied"],
    }


def test_research_contract_positive_is_ready_and_passes():
    result = evaluate_research_contract(complete_case())
    assert result["status"] == "READY"
    assert result["verdict"] == "PASS"
    assert result["completeness_bp"] == 10000


def test_research_contract_missing_claim_ceiling_holds_precondition():
    case = complete_case()
    case["claim_ceiling"] = ""
    result = evaluate_research_contract(case)
    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_PRECONDITION"
    assert result["search_allowed"] is False
