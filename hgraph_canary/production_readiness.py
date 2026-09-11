def evaluate_production_readiness(evidence: dict) -> dict:
    errors = []

    if evidence["runtime_admission"] is not True:
        errors.append("RUNTIME_NOT_ADMITTED")

    if evidence["binary_sha256_expected"] != evidence["binary_sha256_observed"]:
        errors.append("BINARY_IDENTITY_DRIFT")

    if evidence["oracle_sha256_expected"] != evidence["oracle_sha256_observed"]:
        errors.append("ORACLE_IDENTITY_DRIFT")

    if evidence["dependency_manifest_expected"] != evidence["dependency_manifest_observed"]:
        errors.append("DEPENDENCY_MANIFEST_DRIFT")

    if not (
        evidence["baseline_exit_code"] == 0
        and evidence["baseline_state_count"] == 256
        and evidence["baseline_parity_pass"] is True
    ):
        errors.append("BASELINE_REPLAY_FAILED")

    if evidence["baseline_elapsed_ms"] > evidence["max_elapsed_ms"]:
        errors.append("BASELINE_RESOURCE_BOUND_EXCEEDED")

    if evidence["tamper_binary_detected"] is not True:
        errors.append("BINARY_TAMPER_NOT_DETECTED")

    if evidence["tamper_oracle_detected"] is not True:
        errors.append("ORACLE_TAMPER_NOT_DETECTED")

    if evidence["tamper_receipt_detected"] is not True:
        errors.append("RECEIPT_TAMPER_NOT_DETECTED")

    if evidence["dependency_drift_detected"] is not True:
        errors.append("DEPENDENCY_DRIFT_NOT_DETECTED")

    if evidence["rollback_artifact_present"] is not True:
        errors.append("ROLLBACK_ARTIFACT_MISSING")

    if evidence["observability_receipt_complete"] is not True:
        errors.append("OBSERVABILITY_RECEIPT_INCOMPLETE")

    if not (
        evidence["recovery_exit_code"] == 0
        and evidence["recovery_state_count"] == 256
        and evidence["recovery_parity_pass"] is True
    ):
        errors.append("RECOVERY_REPLAY_FAILED")

    if evidence["recovery_binary_sha256"] != evidence["binary_sha256_expected"]:
        errors.append("RECOVERY_BINARY_IDENTITY_MISMATCH")

    if evidence["recovery_output_sha256"] != evidence["expected_output_sha256"]:
        errors.append("RECOVERY_OUTPUT_MISMATCH")

    ready = not errors
    return {
        "verdict": "PASS_BOUNDED_PRODUCTION_READINESS" if ready else "HOLD_BOUNDED_PRODUCTION_READINESS",
        "production_readiness": ready,
        "production_deployment_authorized": False,
        "errors": errors,
    }
