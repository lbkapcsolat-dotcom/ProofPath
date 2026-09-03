"""Requirement-gap evaluation."""

from __future__ import annotations

from alpha6d.contracts import validate_bp, verdict_hold, verdict_pass


_GAP_TYPES = {"MISSING", "PARTIAL", "WEAK_EVIDENCE", "STALE", "CONTRADICTED", "UNBOUND"}


def evaluate_gap(case: dict) -> dict:
    if case.get("identity_collision") is True:
        return {
            **verdict_hold("HOLD_IDENTITY"),
            "gap_type": None,
            "severity_bp": None,
        }

    if case.get("current_known", True) is not True:
        return {
            **verdict_hold("HOLD_PRECONDITION", "G8_PRECONDITION"),
            "gap_type": "UNKNOWN",
            "severity_bp": None,
        }

    importance = validate_bp(case.get("importance_bp", 0), "importance_bp")
    coverage = validate_bp(case.get("coverage_bp", 0), "coverage_bp")
    required = validate_bp(case.get("required_coverage_bp", 10000), "required_coverage_bp")
    deficiency = validate_bp(case.get("evidence_deficiency_bp", 0), "evidence_deficiency_bp")
    freshness = validate_bp(case.get("freshness_factor_bp", 10000), "freshness_factor_bp")

    if case.get("contradicted") is True:
        gap_type = "CONTRADICTED"
    elif case.get("bound", True) is not True:
        gap_type = "UNBOUND"
    elif coverage == 0 and required > 0:
        gap_type = "MISSING"
    elif coverage < required:
        gap_type = "PARTIAL"
    elif freshness < 10000:
        gap_type = "STALE"
    elif deficiency > 0:
        gap_type = "WEAK_EVIDENCE"
    else:
        gap_type = None

    severity = (importance * (10000 - coverage) * deficiency * freshness) // 10**12
    result = {
        **verdict_pass(),
        "gap_type": gap_type,
        "severity_bp": severity,
        "coverage_bp": coverage,
        "required_coverage_bp": required,
        "evidence_deficiency_bp": deficiency,
        "freshness_factor_bp": freshness,
    }
    return result
