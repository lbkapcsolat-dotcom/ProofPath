import json
from pathlib import Path

from alpha6d.canary_runner import run_suite


FIXTURES = Path(__file__).parents[1] / "fixtures" / "canaries.json"
EXPECTED_NAMES = {
    "1A_GAP_POSITIVE", "1B_GAP_NEGATIVE",
    "2A_RESEARCH_POSITIVE", "2B_RESEARCH_NEGATIVE",
    "3A_PRIORITY_POSITIVE", "3B_PRIORITY_NEGATIVE",
    "4A_BATCH_POSITIVE", "4B_BATCH_NEGATIVE",
    "5A_STATE_POSITIVE", "5B_STATE_NEGATIVE",
    "6A_NBA_POSITIVE", "6B_NBA_NEGATIVE",
}


def test_exactly_twelve_named_canaries_match_expected_fields():
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert len(fixtures) == 12
    assert {case["name"] for case in fixtures} == EXPECTED_NAMES

    results = run_suite(fixtures)
    assert len(results) == 12
    for fixture, result in zip(fixtures, results):
        assert result["name"] == fixture["name"]
        for key, expected in fixture["expected"].items():
            assert result["output"][key] == expected, f"{fixture['name']} field {key}"
        assert len(result["receipt_sha256"]) == 64


def test_canary_receipt_hashes_the_full_object_envelope_not_raw_payload():
    from alpha6d.canonical import sha256_hex
    from alpha6d.envelope import make_object_envelope

    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    case = fixtures[0]
    result = run_suite([case])[0]
    envelope = make_object_envelope(
        object_id=case["name"],
        object_type="task",
        payload=case["input"],
        policy_obj=case["policy"],
        evaluated_at=case["evaluated_at"],
    )
    assert result["receipt"]["input_digest_sha256"] == sha256_hex(envelope)
