"""Research-contract precondition evaluation."""

from __future__ import annotations

from alpha6d.contracts import verdict_hold, verdict_pass


_REQUIRED = (
    "question",
    "purpose",
    "claim_ceiling",
    "accepted_source_classes",
    "proof_obligations",
    "stop_conditions",
)


def _present(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return bool(value)
    return value is not None


def evaluate_research_contract(case: dict) -> dict:
    present = [name for name in _REQUIRED if _present(case.get(name))]
    completeness = len(present) * 10000 // len(_REQUIRED)
    missing = [name for name in _REQUIRED if name not in present]
    if missing:
        return {
            **verdict_hold("HOLD_PRECONDITION", "G8_PRECONDITION"),
            "status": "HOLD",
            "search_allowed": False,
            "completeness_bp": completeness,
            "missing_preconditions": missing,
        }
    return {
        **verdict_pass(),
        "status": "READY",
        "search_allowed": True,
        "completeness_bp": completeness,
        "missing_preconditions": [],
    }
