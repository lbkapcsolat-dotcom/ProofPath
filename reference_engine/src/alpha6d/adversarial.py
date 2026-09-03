"""Deterministic adversarial property and metamorphic matrix runner."""

from __future__ import annotations

import random
from typing import Callable

from alpha6d.batch import evaluate_batch
from alpha6d.engine import execute_module
from alpha6d.envelope import make_object_envelope
from alpha6d.gap import evaluate_gap
from alpha6d.nba import select_next_best_action
from alpha6d.state_machine import evaluate_transition

_NOW = "2026-09-01T12:00:00Z"
_GUARD_REASONS = (
    ("schema_ok", "HOLD_SCHEMA"),
    ("authority_ok", "HOLD_AUTHORITY"),
    ("policy_ok", "HOLD_POLICY"),
    ("evidence_ok", "HOLD_EVIDENCE"),
    ("contradiction_free", "HOLD_CONTRADICTION"),
    ("dependencies_ok", "HOLD_DEPENDENCY"),
    ("cost_ok", "HOLD_COST"),
    ("freshness_ok", "HOLD_STALE"),
    ("preconditions_ok", "HOLD_PRECONDITION"),
)


def _envelope(name: str, payload: dict) -> dict:
    return make_object_envelope(
        object_id=name,
        object_type="task",
        payload=payload,
        policy_obj={},
        evaluated_at=_NOW,
    )


def _priority_payload(rng: random.Random) -> dict:
    return {
        "dimensions_bp": [rng.randrange(0, 10001) for _ in range(6)],
        "risk_bp": rng.randrange(0, 10001),
        "uncertainty_bp": rng.randrange(0, 10001),
        "dependency_burden_bp": rng.randrange(0, 10001),
        "cost_burden_bp": rng.randrange(0, 10001),
        "confidence_bp": rng.randrange(0, 10001),
        "max_external_cost_microunits": 0,
        "estimated_external_cost_microunits": 0,
    }


def _action(action_id: str, size: int, score: int, *, safe: bool = True, origin: str = "OPEN_GAP") -> dict:
    return {
        "action_id": action_id,
        "origin": origin,
        "hard_guard_pass": safe,
        "action_size_units": size,
        "blocker_reduction_bp": score,
        "evidence_gain_bp": score,
        "downstream_unlock_bp": score,
        "reversibility_bp": score,
        "confidence_bp": score,
        "information_gain_bp": score,
        "penalty_bp": 0,
    }


def _failure(case_index: int, expected: str, observed: object) -> dict:
    return {"case_index": case_index, "expected": expected, "observed": observed}


def _run_unknown(count: int, rng: random.Random) -> list[dict]:
    failures = []
    for i in range(count):
        result = evaluate_gap({
            "current_known": False,
            "importance_bp": rng.randrange(0, 10001),
            "coverage_bp": rng.randrange(0, 10001),
            "required_coverage_bp": rng.randrange(0, 10001),
            "evidence_deficiency_bp": rng.randrange(0, 10001),
            "freshness_factor_bp": rng.randrange(0, 10001),
        })
        observed = (result.get("verdict"), result.get("reason_code"), result.get("gap_type"), result.get("severity_bp"))
        expected = ("HOLD", "HOLD_PRECONDITION", "UNKNOWN", None)
        if observed != expected:
            failures.append(_failure(i, str(expected), observed))
    return failures


def _run_hold_dominance(count: int, rng: random.Random) -> list[dict]:
    failures = []
    for i in range(count):
        signal, reason = _GUARD_REASONS[i % len(_GUARD_REASONS)]
        payload = _priority_payload(rng)
        # Metamorphic inflation: the candidate can be made arbitrarily attractive.
        if i % 2:
            payload["dimensions_bp"] = [10000] * 6
            payload["confidence_bp"] = 10000
            payload["risk_bp"] = 0
            payload["uncertainty_bp"] = 0
            payload["dependency_burden_bp"] = 0
            payload["cost_burden_bp"] = 0
        result = execute_module("PRIORITY_SCORE", _envelope(f"HOLD_{i}", payload), {signal: False})
        observed = (result.get("verdict"), result.get("reason_code"), result.get("score_bp"), result.get("eligible"))
        expected = ("HOLD", reason, None, False)
        if observed != expected:
            failures.append(_failure(i, str(expected), observed))
    return failures


def _run_authority(count: int, rng: random.Random) -> list[dict]:
    failures = []
    for i in range(count):
        env = _envelope(f"AUTH_{i}", _priority_payload(rng))
        variant = i % 4
        if variant == 0:
            env["constraints"]["mutation_allowed"] = True
            expected = ("HOLD", "HOLD_AUTHORITY", None)
        elif variant == 1:
            env["constraints"]["external_communication_allowed"] = True
            expected = ("HOLD", "HOLD_POLICY", None)
        elif variant == 2:
            env["authority"]["mode"] = "BYPASS"
            expected = ("HOLD", "HOLD_SCHEMA", None)
        else:
            env["authority"]["external_action_allowed"] = "false"
            expected = ("HOLD", "HOLD_SCHEMA", None)
        result = execute_module("PRIORITY_SCORE", env)
        observed = (result.get("verdict"), result.get("reason_code"), result.get("score_bp"))
        if observed != expected:
            failures.append(_failure(i, str(expected), observed))
    return failures


def _state(lifecycle: str, verification: str, authority: str) -> dict:
    return {"lifecycle": lifecycle, "verification": verification, "authority": authority}


def _run_state(count: int, rng: random.Random) -> list[dict]:
    del rng
    failures = []
    cases = (
        # legal adjacent lifecycle transition
        ({"from": _state("PROCESSED", "VERIFIED", "NON_CANONICAL"), "to": _state("REVIEW_READY", "VERIFIED", "NON_CANONICAL"), "required_evidence": ["e://1"], "receipt_ref": "r://1", "actor_scope": "ANALYZE"}, ("PASS", "PASS")),
        # lifecycle jump
        ({"from": _state("DISCOVERED", "VERIFIED", "NON_CANONICAL"), "to": _state("PROCESSED", "VERIFIED", "NON_CANONICAL"), "required_evidence": ["e://1"], "receipt_ref": "r://1", "actor_scope": "ANALYZE"}, ("HOLD", "HOLD_PRECONDITION")),
        # proof manufacture
        ({"from": _state("PROCESSED", "UNVERIFIED", "NON_CANONICAL"), "to": _state("REVIEW_READY", "VERIFIED", "NON_CANONICAL"), "required_evidence": [], "receipt_ref": "r://1", "actor_scope": "ANALYZE"}, ("HOLD", "HOLD_EVIDENCE")),
        # authority jump
        ({"from": _state("PROCESSED", "VERIFIED", "NON_CANONICAL"), "to": _state("PROCESSED", "VERIFIED", "CANONICAL"), "required_evidence": ["e://1"], "receipt_ref": "r://1", "actor_scope": "PROMOTE"}, ("HOLD", "HOLD_PRECONDITION")),
        # authority backtrack
        ({"from": _state("PROCESSED", "VERIFIED", "CANONICAL"), "to": _state("PROCESSED", "VERIFIED", "CANDIDATE"), "required_evidence": ["e://1"], "receipt_ref": "r://1", "actor_scope": "PROMOTE"}, ("HOLD", "HOLD_PRECONDITION")),
        # adjacent authority transition but wrong scope
        ({"from": _state("PROCESSED", "VERIFIED", "NON_CANONICAL"), "to": _state("PROCESSED", "VERIFIED", "CANDIDATE"), "required_evidence": ["e://1"], "receipt_ref": "r://1", "actor_scope": "ANALYZE"}, ("HOLD", "HOLD_AUTHORITY")),
        # canonical from unverified
        ({"from": _state("PROCESSED", "UNVERIFIED", "CANDIDATE"), "to": _state("PROCESSED", "UNVERIFIED", "CANONICAL"), "required_evidence": ["e://1"], "receipt_ref": "r://1", "actor_scope": "PROMOTE"}, ("HOLD", "HOLD_EVIDENCE")),
        # missing receipt
        ({"from": _state("PROCESSED", "VERIFIED", "NON_CANONICAL"), "to": _state("REVIEW_READY", "VERIFIED", "NON_CANONICAL"), "required_evidence": ["e://1"], "receipt_ref": "", "actor_scope": "ANALYZE"}, ("HOLD", "HOLD_EVIDENCE")),
    )
    for i in range(count):
        case, expected = cases[i % len(cases)]
        result = evaluate_transition(case)
        observed = (result.get("verdict"), result.get("reason_code"))
        if observed != expected:
            failures.append(_failure(i, str(expected), observed))
    return failures


def _run_batch(count: int, rng: random.Random) -> list[dict]:
    failures = []
    for i in range(count):
        variant = i % 4
        if variant == 0:
            jobs = [
                {"job_id": "A", "required": True, "verdict": "PASS"},
                {"job_id": "B", "required": True, "verdict": "PASS"},
                {"job_id": "OPT", "required": False, "verdict": "HOLD"},
            ]
            first = evaluate_batch({"jobs": jobs})
            rng.shuffle(jobs)
            second = evaluate_batch({"jobs": jobs})
            ok = first.get("verdict") == second.get("verdict") == "PASS" and first.get("batch_status") == second.get("batch_status") == "PASS_2_OF_2"
            observed = (first.get("verdict"), first.get("batch_status"), second.get("verdict"), second.get("batch_status"))
            expected = "permutation invariant PASS_2_OF_2"
        elif variant == 1:
            jobs = [
                {"job_id": "A", "required": True, "verdict": "PASS"},
                {"job_id": "B", "required": True, "verdict": "HOLD"},
                {"job_id": "OPT", "required": False, "verdict": "PASS"},
            ]
            result = evaluate_batch({"jobs": jobs})
            ok = result.get("verdict") == "HOLD" and result.get("batch_status") == "HOLD_1_OF_2"
            observed = (result.get("verdict"), result.get("batch_status"))
            expected = "required HOLD => HOLD_1_OF_2"
        elif variant == 2:
            result = evaluate_batch({"jobs": [
                {"job_id": "DUP", "required": True, "verdict": "PASS"},
                {"job_id": "DUP", "required": True, "verdict": "PASS"},
            ]})
            ok = result.get("verdict") == "HOLD" and result.get("reason_code") == "HOLD_IDENTITY"
            observed = (result.get("verdict"), result.get("reason_code"), result.get("batch_status"))
            expected = "duplicate required job identity => HOLD_IDENTITY"
        else:
            result = evaluate_batch({"jobs": [{"job_id": "OPT", "required": False, "verdict": "PASS"}]})
            ok = result.get("verdict") == "HOLD" and result.get("batch_status") == "HOLD_0_OF_0"
            observed = (result.get("verdict"), result.get("batch_status"))
            expected = "no required jobs => HOLD_0_OF_0"
        if not ok:
            failures.append(_failure(i, expected, observed))
    return failures


def _run_nba(count: int, rng: random.Random) -> list[dict]:
    failures = []
    for i in range(count):
        variant = i % 4
        if variant == 0:
            actions = [
                _action("B", 1, 7000),
                _action("A", 1, 7000),
                _action("BIG", 2, 10000),
                _action("UNSAFE", 0, 10000, safe=False),
            ]
            first = select_next_best_action({"actions": actions})
            rng.shuffle(actions)
            second = select_next_best_action({"actions": actions})
            ok = first.get("selected_action_id") == second.get("selected_action_id") == "A"
            observed = (first.get("selected_action_id"), second.get("selected_action_id"))
            expected = "permutation invariant selection A"
        elif variant == 1:
            base = select_next_best_action({"actions": [_action("SAFE", 1, 1200)]})
            transformed = select_next_best_action({"actions": [
                _action("SAFE", 1, 1200),
                _action("UNSAFE", 0, 10000, safe=False),
                _action("ARBITRARY", 0, 10000, origin="ARBITRARY"),
            ]})
            ok = base.get("selected_action_id") == transformed.get("selected_action_id") == "SAFE"
            observed = (base.get("selected_action_id"), transformed.get("selected_action_id"))
            expected = "unsafe/arbitrary insertion invariant SAFE"
        elif variant == 2:
            result = select_next_best_action({"actions": [
                _action("DUP", 1, 1000),
                _action("DUP", 1, 9000),
            ]})
            ok = result.get("verdict") == "HOLD" and result.get("reason_code") == "HOLD_IDENTITY"
            observed = (result.get("verdict"), result.get("reason_code"), result.get("selected_action_id"))
            expected = "duplicate action identity => HOLD_IDENTITY"
        else:
            result = select_next_best_action({"actions": [_action("X", 1, 10000, origin="ARBITRARY")]})
            ok = result.get("verdict") == "HOLD" and result.get("reason_code") == "HOLD_NO_SAFE_ACTION"
            observed = (result.get("verdict"), result.get("reason_code"))
            expected = "arbitrary-only => HOLD_NO_SAFE_ACTION"
        if not ok:
            failures.append(_failure(i, expected, observed))
    return failures


_RUNNERS: dict[str, Callable[[int, random.Random], list[dict]]] = {
    "I01_UNKNOWN_NOT_MISSING": _run_unknown,
    "I03_HOLD_DOMINATES_SCORE": _run_hold_dominance,
    "I05_AUTHORITY_FAIL_CLOSED": _run_authority,
    "I09_STATE_TRANSITION_PROOF": _run_state,
    "I08_BATCH_REQUIRED_FAIL_CLOSED": _run_batch,
    "I12_NBA_SMALLEST_SAFE": _run_nba,
}


def run_adversarial_matrix(matrix: dict) -> dict:
    seed = matrix["seed"]
    family_reports = []
    total = passed = failed = 0
    for index, family in enumerate(matrix["families"]):
        family_id = family["id"]
        count = family["case_count"]
        rng = random.Random(seed + index)
        failures = _RUNNERS[family_id](count, rng)
        failed_count = len(failures)
        passed_count = count - failed_count
        family_reports.append({
            "id": family_id,
            "case_count": count,
            "passed_case_count": passed_count,
            "failed_case_count": failed_count,
            "verdict": "PASS" if failed_count == 0 else "HOLD",
            "failures": failures[:16],
        })
        total += count
        passed += passed_count
        failed += failed_count

    return {
        "matrix_schema": matrix["schema"],
        "engine_contract": matrix["engine_contract"],
        "seed": seed,
        "family_count": len(family_reports),
        "case_count": total,
        "passed_case_count": passed,
        "failed_case_count": failed,
        "verdict": "PASS" if failed == 0 else "HOLD",
        "families": family_reports,
    }
