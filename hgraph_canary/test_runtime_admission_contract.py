from hgraph_canary.runtime_admission import evaluate_runtime_admission


def valid_evidence():
    return {
        "source_commit_a": "proofpath-head",
        "source_commit_b": "proofpath-head",
        "hgraph_commit_a": "hgraph-head",
        "hgraph_commit_b": "hgraph-head",
        "binary_sha256_a": "bin-sha",
        "binary_sha256_b": "bin-sha",
        "oracle_sha256_a": "oracle-sha",
        "oracle_sha256_b": "oracle-sha",
        "output_sha256_a": "output-sha",
        "output_sha256_b": "output-sha",
        "expected_output_sha256": "output-sha",
        "state_count_a": 256,
        "state_count_b": 256,
        "parity_pass_a": True,
        "parity_pass_b": True,
    }


def test_admits_only_exact_custody_and_two_replays():
    result = evaluate_runtime_admission(valid_evidence())
    assert result["verdict"] == "PASS_RUNTIME_ADMISSION"
    assert result["runtime_admission"] is True
    assert result["errors"] == []


def test_holds_on_binary_byte_mismatch():
    evidence = valid_evidence()
    evidence["binary_sha256_b"] = "different-bin"
    result = evaluate_runtime_admission(evidence)
    assert result["verdict"] == "HOLD_RUNTIME_ADMISSION"
    assert "BINARY_SHA256_MISMATCH" in result["errors"]


def test_holds_on_oracle_mismatch():
    evidence = valid_evidence()
    evidence["oracle_sha256_b"] = "different-oracle"
    result = evaluate_runtime_admission(evidence)
    assert "ORACLE_SHA256_MISMATCH" in result["errors"]


def test_holds_on_replay_output_mismatch():
    evidence = valid_evidence()
    evidence["output_sha256_b"] = "different-output"
    result = evaluate_runtime_admission(evidence)
    assert "OUTPUT_SHA256_MISMATCH" in result["errors"]


def test_holds_if_output_does_not_match_expected_oracle_output():
    evidence = valid_evidence()
    evidence["expected_output_sha256"] = "expected-different"
    result = evaluate_runtime_admission(evidence)
    assert "OUTPUT_NOT_ORACLE_EXPECTED" in result["errors"]


def test_holds_if_either_replay_is_not_256_state_pass():
    evidence = valid_evidence()
    evidence["state_count_b"] = 255
    evidence["parity_pass_b"] = False
    result = evaluate_runtime_admission(evidence)
    assert "REPLAY_B_NOT_256_PASS" in result["errors"]


def test_holds_if_source_identity_drifted_between_runners():
    evidence = valid_evidence()
    evidence["source_commit_b"] = "other-proofpath-head"
    evidence["hgraph_commit_b"] = "other-hgraph-head"
    result = evaluate_runtime_admission(evidence)
    assert "SOURCE_COMMIT_MISMATCH" in result["errors"]
    assert "HGRAPH_COMMIT_MISMATCH" in result["errors"]
