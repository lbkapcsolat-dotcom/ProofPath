from alpha6d.guards import evaluate_guards


def all_clear():
    return {
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


def test_guard_kernel_passes_when_all_hard_guards_clear():
    assert evaluate_guards(all_clear())["verdict"] == "PASS"


def test_guard_kernel_selects_first_failure_by_precedence_and_reports_all():
    signals = all_clear()
    signals["authority_ok"] = False
    signals["cost_ok"] = False
    signals["preconditions_ok"] = False
    result = evaluate_guards(signals)
    assert result == {
        "verdict": "HOLD",
        "reason_code": "HOLD_AUTHORITY",
        "first_failed_guard": "G1_AUTHORITY",
        "failed_guards": ["G1_AUTHORITY", "G6_COST", "G8_PRECONDITION"],
        "eligible_for_scoring": False,
    }


def test_schema_failure_has_highest_precedence():
    signals = all_clear()
    for key in signals:
        signals[key] = False
    result = evaluate_guards(signals)
    assert result["first_failed_guard"] == "G0_SCHEMA"
    assert result["reason_code"] == "HOLD_SCHEMA"
