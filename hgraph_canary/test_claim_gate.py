import hashlib
import itertools
import json
from pathlib import Path

import pytest
from hgraph.test import eval_node


FIXTURE_PATH = Path(__file__).with_name("wolfram_oracle_v1.json")


def load_claim_gate():
    try:
        from hgraph_canary.claim_gate import claim_gate
    except ModuleNotFoundError as exc:
        pytest.fail(f"claim_gate implementation missing: {exc}")
    return claim_gate


def run_case(
    *,
    current_pointer_present: bool = True,
    pointer_matches_root: bool = True,
    requested_claim_rank: int = 3,
    evidence_level_rank: int = 3,
    independent_validation: bool = True,
    irreversible_action: bool = False,
    human_gate: bool = False,
    rollback_plan: bool = True,
):
    claim_gate = load_claim_gate()
    return eval_node(
        claim_gate,
        [current_pointer_present],
        [pointer_matches_root],
        [requested_claim_rank],
        [evidence_level_rank],
        [independent_validation],
        [irreversible_action],
        [human_gate],
        [rollback_plan],
        __elide__=True,
    )


def test_baseline_authoritative_case_passes():
    assert run_case() == ["PASS"]


def test_missing_current_pointer_fails_closed():
    assert run_case(current_pointer_present=False) == ["HOLD:MISSING_CURRENT_POINTER"]


def test_authority_drift_fails_closed():
    assert run_case(pointer_matches_root=False) == ["HOLD:AUTHORITY_DRIFT"]


def test_production_overclaim_fails_closed():
    assert run_case(
        requested_claim_rank=6,
        evidence_level_rank=3,
        independent_validation=False,
    ) == ["HOLD:CLAIM_EXCEEDS_EVIDENCE"]


def test_irreversible_without_human_gate_fails_closed():
    assert run_case(
        irreversible_action=True,
        human_gate=False,
        rollback_plan=False,
    ) == ["HOLD:IRREVERSIBLE_WITHOUT_HUMAN_GATE"]


def test_wolfram_oracle_fixture_hash_is_exact():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    vector = fixture["vector"]
    assert len(vector) == fixture["total_states"] == 256
    assert hashlib.sha256(vector.encode("utf-8")).hexdigest() == fixture["vector_sha256"]


def test_hgraph_matches_wolfram_oracle_all_256_states():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    domains = fixture["domains"]
    states = list(itertools.product(*domains))
    assert len(states) == fixture["total_states"] == 256

    code_map = fixture["code_map"]
    observed_codes = []

    for state in states:
        result = run_case(
            current_pointer_present=state[0],
            pointer_matches_root=state[1],
            requested_claim_rank=state[2],
            evidence_level_rank=state[3],
            independent_validation=state[4],
            irreversible_action=state[5],
            human_gate=state[6],
            rollback_plan=state[7],
        )
        assert len(result) == 1
        observed_codes.append(code_map[result[0]])

    observed_vector = "".join(observed_codes)
    assert observed_vector == fixture["vector"]
    assert hashlib.sha256(observed_vector.encode("utf-8")).hexdigest() == fixture["vector_sha256"]
