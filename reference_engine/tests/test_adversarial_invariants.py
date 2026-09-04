import itertools
import random

from alpha6d.batch import evaluate_batch
from alpha6d.engine import execute_module
from alpha6d.envelope import make_object_envelope
from alpha6d.gap import evaluate_gap
from alpha6d.nba import select_next_best_action
from alpha6d.state_machine import evaluate_transition

NOW = "2026-09-01T12:00:00Z"


def envelope(name, payload, policy=None):
    return make_object_envelope(
        object_id=name,
        object_type="task",
        payload=payload,
        policy_obj=policy or {},
        evaluated_at=NOW,
    )


def priority_payload(**overrides):
    payload = {
        "dimensions_bp": [10000] * 6,
        "risk_bp": 0,
        "uncertainty_bp": 0,
        "dependency_burden_bp": 0,
        "cost_burden_bp": 0,
        "confidence_bp": 10000,
        "max_external_cost_microunits": 0,
        "estimated_external_cost_microunits": 0,
    }
    payload.update(overrides)
    return payload


def action(action_id, *, size=1, score=5000, safe=True, origin="OPEN_GAP"):
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


def test_i01_unknown_never_collapses_to_missing_under_numeric_metamorphisms():
    rng = random.Random(6101)
    for _ in range(128):
        case = {
            "current_known": False,
            "importance_bp": rng.randrange(0, 10001),
            "coverage_bp": rng.randrange(0, 10001),
            "required_coverage_bp": rng.randrange(0, 10001),
            "evidence_deficiency_bp": rng.randrange(0, 10001),
            "freshness_factor_bp": rng.randrange(0, 10001),
        }
        result = evaluate_gap(case)
        assert result["verdict"] == "HOLD"
        assert result["reason_code"] == "HOLD_PRECONDITION"
        assert result["gap_type"] == "UNKNOWN"
        assert result["severity_bp"] is None


def test_i01_known_zero_coverage_is_missing_not_unknown():
    result = evaluate_gap({
        "current_known": True,
        "importance_bp": 10000,
        "coverage_bp": 0,
        "required_coverage_bp": 10000,
        "evidence_deficiency_bp": 10000,
        "freshness_factor_bp": 10000,
    })
    assert result["verdict"] == "PASS"
    assert result["gap_type"] == "MISSING"


def test_i03_hard_hold_dominates_maximum_priority_score_for_every_guard_position():
    guard_to_reason = {
        "schema_ok": "HOLD_SCHEMA",
        "authority_ok": "HOLD_AUTHORITY",
        "policy_ok": "HOLD_POLICY",
        "evidence_ok": "HOLD_EVIDENCE",
        "contradiction_free": "HOLD_CONTRADICTION",
        "dependencies_ok": "HOLD_DEPENDENCY",
        "cost_ok": "HOLD_COST",
        "freshness_ok": "HOLD_STALE",
        "preconditions_ok": "HOLD_PRECONDITION",
    }
    env = envelope("HOLD_DOMINANCE", priority_payload())
    for signal, reason in guard_to_reason.items():
        result = execute_module("PRIORITY_SCORE", env, guard_signals={signal: False})
        assert result["verdict"] == "HOLD"
        assert result["reason_code"] == reason
        assert result["score_bp"] is None
        assert result["eligible"] is False


def test_fail_closed_priority_malformed_basis_points_returns_hold_not_exception():
    env = envelope("BAD_BP", priority_payload(risk_bp="1000"))
    result = execute_module("PRIORITY_SCORE", env)
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_SCHEMA"
    assert result["score_bp"] is None


def test_authority_read_only_hold_is_invariant_to_payload_score_inflation():
    rng = random.Random(6102)
    for _ in range(64):
        dims = [rng.randrange(0, 10001) for _ in range(6)]
        env = envelope("AUTHORITY_HOLD", priority_payload(dimensions_bp=dims))
        env["constraints"]["mutation_allowed"] = True
        result = execute_module("PRIORITY_SCORE", env)
        assert result["reason_code"] == "HOLD_AUTHORITY"
        assert result["score_bp"] is None


def test_state_machine_cannot_manufacture_verified_state_without_evidence():
    result = evaluate_transition({
        "from": {"lifecycle": "PROCESSED", "verification": "UNVERIFIED", "authority": "NON_CANONICAL"},
        "to": {"lifecycle": "REVIEW_READY", "verification": "VERIFIED", "authority": "NON_CANONICAL"},
        "required_evidence": [],
        "receipt_ref": "receipt://state-proof",
        "actor_scope": "ANALYZE",
    })
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_EVIDENCE"
    assert result["transition_allowed"] is False


def test_state_lifecycle_jump_and_backtrack_are_always_hold():
    base = {"verification": "VERIFIED", "authority": "NON_CANONICAL"}
    invalid_pairs = [
        ("DISCOVERED", "PROCESSED"),
        ("REVIEW_READY", "ACQUIRED"),
        ("PROCESSED", "RELEASED"),
    ]
    for before, after in invalid_pairs:
        result = evaluate_transition({
            "from": {**base, "lifecycle": before},
            "to": {**base, "lifecycle": after},
            "required_evidence": ["evidence://x"],
            "receipt_ref": "receipt://x",
            "actor_scope": "ANALYZE",
        })
        assert result["verdict"] == "HOLD"
        assert result["reason_code"] == "HOLD_PRECONDITION"


def test_batch_required_result_is_permutation_invariant():
    jobs = [
        {"required": True, "verdict": "PASS"},
        {"required": True, "verdict": "HOLD"},
        {"required": True, "verdict": "PASS"},
        {"required": False, "verdict": "HOLD"},
    ]
    expected = evaluate_batch({"jobs": jobs})
    for permutation in itertools.permutations(jobs):
        result = evaluate_batch({"jobs": list(permutation)})
        assert result["verdict"] == expected["verdict"]
        assert result["batch_status"] == expected["batch_status"]


def test_batch_optional_hold_never_changes_required_pass():
    base = evaluate_batch({"jobs": [{"required": True, "verdict": "PASS"}]})
    transformed = evaluate_batch({
        "jobs": [
            {"required": True, "verdict": "PASS"},
            {"required": False, "verdict": "HOLD"},
            {"required": False, "verdict": "HOLD"},
        ]
    })
    assert base["verdict"] == transformed["verdict"] == "PASS"
    assert base["batch_status"] == transformed["batch_status"] == "PASS_1_OF_1"


def test_fail_closed_batch_malformed_job_returns_hold_not_exception():
    env = envelope("BAD_BATCH", {"jobs": [None]})
    result = execute_module("BATCH_ENGINE", env)
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_SCHEMA"


def test_nba_selection_is_permutation_invariant():
    actions = [
        action("B", size=1, score=7000),
        action("A", size=1, score=7000),
        action("SMALLER_SCORE", size=1, score=6000),
        action("BIG", size=2, score=10000),
        action("UNSAFE", size=1, score=10000, safe=False),
    ]
    for permutation in itertools.permutations(actions):
        result = select_next_best_action({"actions": list(permutation)})
        assert result["selected_action_id"] == "A"
        assert result["selected_action_size_units"] == 1


def test_nba_unsafe_or_arbitrary_dominant_candidates_cannot_change_selection():
    base = select_next_best_action({"actions": [action("SAFE", size=1, score=1000)]})
    transformed = select_next_best_action({
        "actions": [
            action("SAFE", size=1, score=1000),
            action("UNSAFE", size=0, score=10000, safe=False),
            action("ARBITRARY", size=0, score=10000, origin="ARBITRARY"),
        ]
    })
    assert base["selected_action_id"] == transformed["selected_action_id"] == "SAFE"


def test_fail_closed_nba_malformed_candidate_returns_hold_not_exception():
    malformed = action("BAD", size=1, score=5000)
    malformed["evidence_gain_bp"] = "lots"
    env = envelope("BAD_NBA", {"actions": [malformed]})
    result = execute_module("NBA_ENGINE", env)
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_SCHEMA"
    assert result["selected_action_id"] is None


def test_authority_envelope_rejects_unknown_mode_and_non_boolean_action_flag():
    env = envelope("BAD_AUTH_MODE", priority_payload())
    env["authority"]["mode"] = "BYPASS"
    result = execute_module("PRIORITY_SCORE", env)
    assert result["reason_code"] == "HOLD_SCHEMA"
    assert result["score_bp"] is None

    env = envelope("BAD_AUTH_FLAG", priority_payload())
    env["authority"]["external_action_allowed"] = "false"
    result = execute_module("PRIORITY_SCORE", env)
    assert result["reason_code"] == "HOLD_SCHEMA"
    assert result["score_bp"] is None


def test_state_machine_rejects_authority_jump_and_backtrack():
    jump = evaluate_transition({
        "from": {"lifecycle": "PROCESSED", "verification": "VERIFIED", "authority": "NON_CANONICAL"},
        "to": {"lifecycle": "PROCESSED", "verification": "VERIFIED", "authority": "CANONICAL"},
        "required_evidence": ["evidence://proof"],
        "receipt_ref": "receipt://proof",
        "actor_scope": "PROMOTE",
    })
    assert jump["reason_code"] == "HOLD_PRECONDITION"

    backtrack = evaluate_transition({
        "from": {"lifecycle": "PROCESSED", "verification": "VERIFIED", "authority": "CANONICAL"},
        "to": {"lifecycle": "PROCESSED", "verification": "VERIFIED", "authority": "CANDIDATE"},
        "required_evidence": ["evidence://proof"],
        "receipt_ref": "receipt://proof",
        "actor_scope": "PROMOTE",
    })
    assert backtrack["reason_code"] == "HOLD_PRECONDITION"


def test_batch_rejects_duplicate_explicit_job_identities():
    result = evaluate_batch({"jobs": [
        {"job_id": "DUP", "required": True, "verdict": "PASS"},
        {"job_id": "DUP", "required": True, "verdict": "PASS"},
    ]})
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_IDENTITY"
    assert result["batch_status"] == "HOLD_0_OF_2"


def test_nba_rejects_duplicate_explicit_action_identities():
    result = select_next_best_action({"actions": [
        action("DUP", size=1, score=1000),
        action("DUP", size=1, score=9000),
    ]})
    assert result["verdict"] == "HOLD"
    assert result["reason_code"] == "HOLD_IDENTITY"
    assert result["selected_action_id"] is None
