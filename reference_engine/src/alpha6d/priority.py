"""Six-dimensional deterministic priority scoring."""

from __future__ import annotations

from alpha6d.contracts import validate_bp, verdict_hold, verdict_pass


DIMENSION_WEIGHTS = (2000, 1500, 1500, 1500, 1500, 2000)
PENALTY_WEIGHTS = {
    "risk_bp": 3000,
    "uncertainty_bp": 2500,
    "dependency_burden_bp": 2000,
    "cost_burden_bp": 2500,
}


def evaluate_priority(case: dict) -> dict:
    max_cost = case.get("max_external_cost_microunits")
    estimated_cost = case.get("estimated_external_cost_microunits", 0)
    if max_cost is not None and estimated_cost > max_cost:
        return {
            **verdict_hold("HOLD_COST", "G6_COST"),
            "eligible": False,
            "utility_bp": None,
            "penalty_bp": None,
            "score_bp": None,
        }

    dimensions = case.get("dimensions_bp", [])
    if len(dimensions) != 6:
        return {
            **verdict_hold("HOLD_SCHEMA", "G0_SCHEMA"),
            "eligible": False,
            "utility_bp": None,
            "penalty_bp": None,
            "score_bp": None,
        }
    dims = [validate_bp(v, f"dimensions_bp[{i}]") for i, v in enumerate(dimensions)]
    confidence = validate_bp(case.get("confidence_bp", 0), "confidence_bp")
    penalty_inputs = {
        name: validate_bp(case.get(name, 0), name)
        for name in PENALTY_WEIGHTS
    }

    utility = sum(weight * value for weight, value in zip(DIMENSION_WEIGHTS, dims)) // 10000
    penalty = sum(PENALTY_WEIGHTS[name] * value for name, value in penalty_inputs.items()) // 10000
    base = max(utility - penalty, 0)
    score = base * confidence // 10000
    return {
        **verdict_pass(),
        "eligible": True,
        "utility_bp": utility,
        "penalty_bp": penalty,
        "score_bp": score,
    }
