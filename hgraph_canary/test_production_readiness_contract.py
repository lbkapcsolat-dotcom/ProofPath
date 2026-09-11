from hgraph_canary.production_readiness import evaluate_production_readiness


def valid_evidence():
    return {
        "runtime_admission": True,
        "binary_sha256_expected": "bin-sha",
        "binary_sha256_observed": "bin-sha",
        "oracle_sha256_expected": "oracle-sha",
        "oracle_sha256_observed": "oracle-sha",
        "dependency_manifest_expected": "deps-sha",
        "dependency_manifest_observed": "deps-sha",
        "baseline_exit_code": 0,
        "baseline_state_count": 256,
        "baseline_parity_pass": True,
        "baseline_elapsed_ms": 50,
        "max_elapsed_ms": 5000,
        "tamper_binary_detected": True,
        "tamper_oracle_detected": True,
        "tamper_receipt_detected": True,
        "dependency_drift_detected": True,
        "rollback_artifact_present": True,
        "observability_receipt_complete": True,
        "recovery_exit_code": 0,
        "recovery_state_count": 256,
        "recovery_parity_pass": True,
        "recovery_binary_sha256": "bin-sha",
        "recovery_output_sha256": "output-sha",
        "expected_output_sha256": "output-sha",
    }


def test_passes_only_complete_bounded_production_readiness_evidence():
    result = evaluate_production_readiness(valid_evidence())
    assert result["verdict"] == "PASS_BOUNDED_PRODUCTION_READINESS"
    assert result["production_readiness"] is True
    assert result["production_deployment_authorized"] is False
    assert result["errors"] == []


def test_holds_without_runtime_admission():
    evidence = valid_evidence()
    evidence["runtime_admission"] = False
    result = evaluate_production_readiness(evidence)
    assert "RUNTIME_NOT_ADMITTED" in result["errors"]


def test_holds_on_identity_or_dependency_drift():
    evidence = valid_evidence()
    evidence["binary_sha256_observed"] = "other-bin"
    evidence["oracle_sha256_observed"] = "other-oracle"
    evidence["dependency_manifest_observed"] = "other-deps"
    result = evaluate_production_readiness(evidence)
    assert "BINARY_IDENTITY_DRIFT" in result["errors"]
    assert "ORACLE_IDENTITY_DRIFT" in result["errors"]
    assert "DEPENDENCY_MANIFEST_DRIFT" in result["errors"]


def test_holds_on_baseline_failure_or_resource_bound_violation():
    evidence = valid_evidence()
    evidence["baseline_exit_code"] = 1
    evidence["baseline_state_count"] = 255
    evidence["baseline_parity_pass"] = False
    evidence["baseline_elapsed_ms"] = 5001
    result = evaluate_production_readiness(evidence)
    assert "BASELINE_REPLAY_FAILED" in result["errors"]
    assert "BASELINE_RESOURCE_BOUND_EXCEEDED" in result["errors"]


def test_holds_if_any_adversarial_tamper_is_not_detected():
    evidence = valid_evidence()
    evidence["tamper_binary_detected"] = False
    evidence["tamper_oracle_detected"] = False
    evidence["tamper_receipt_detected"] = False
    evidence["dependency_drift_detected"] = False
    result = evaluate_production_readiness(evidence)
    assert "BINARY_TAMPER_NOT_DETECTED" in result["errors"]
    assert "ORACLE_TAMPER_NOT_DETECTED" in result["errors"]
    assert "RECEIPT_TAMPER_NOT_DETECTED" in result["errors"]
    assert "DEPENDENCY_DRIFT_NOT_DETECTED" in result["errors"]


def test_holds_without_rollback_observability_or_exact_recovery():
    evidence = valid_evidence()
    evidence["rollback_artifact_present"] = False
    evidence["observability_receipt_complete"] = False
    evidence["recovery_exit_code"] = 2
    evidence["recovery_state_count"] = 255
    evidence["recovery_parity_pass"] = False
    evidence["recovery_binary_sha256"] = "other-bin"
    evidence["recovery_output_sha256"] = "other-output"
    result = evaluate_production_readiness(evidence)
    assert "ROLLBACK_ARTIFACT_MISSING" in result["errors"]
    assert "OBSERVABILITY_RECEIPT_INCOMPLETE" in result["errors"]
    assert "RECOVERY_REPLAY_FAILED" in result["errors"]
    assert "RECOVERY_BINARY_IDENTITY_MISMATCH" in result["errors"]
    assert "RECOVERY_OUTPUT_MISMATCH" in result["errors"]
