import hashlib

from alpha6d.batch import evaluate_batch, job_key


def test_job_key_is_sha256_of_exact_concatenation():
    expected = hashlib.sha256(b"inputcontractpolicy").hexdigest()
    assert job_key("input", "contract", "policy") == expected


def test_batch_positive_canary_is_pass_3_of_3():
    result = evaluate_batch({
        "jobs": [
            {"required": True, "verdict": "PASS"},
            {"required": True, "verdict": "PASS"},
            {"required": True, "verdict": "PASS"},
        ]
    })
    assert result["verdict"] == "PASS"
    assert result["batch_status"] == "PASS_3_OF_3"


def test_batch_negative_canary_is_hold_2_of_3():
    result = evaluate_batch({
        "jobs": [
            {"required": True, "verdict": "PASS"},
            {"required": True, "verdict": "HOLD"},
            {"required": True, "verdict": "PASS"},
        ]
    })
    assert result["verdict"] == "HOLD"
    assert result["batch_status"] == "HOLD_2_OF_3"
