def evaluate_runtime_admission(evidence: dict) -> dict:
    errors = []

    if evidence["source_commit_a"] != evidence["source_commit_b"]:
        errors.append("SOURCE_COMMIT_MISMATCH")

    if evidence["hgraph_commit_a"] != evidence["hgraph_commit_b"]:
        errors.append("HGRAPH_COMMIT_MISMATCH")

    if evidence["binary_sha256_a"] != evidence["binary_sha256_b"]:
        errors.append("BINARY_SHA256_MISMATCH")

    if evidence["oracle_sha256_a"] != evidence["oracle_sha256_b"]:
        errors.append("ORACLE_SHA256_MISMATCH")

    if evidence["output_sha256_a"] != evidence["output_sha256_b"]:
        errors.append("OUTPUT_SHA256_MISMATCH")

    if not (
        evidence["output_sha256_a"] == evidence["expected_output_sha256"]
        and evidence["output_sha256_b"] == evidence["expected_output_sha256"]
    ):
        errors.append("OUTPUT_NOT_ORACLE_EXPECTED")

    if not (evidence["state_count_a"] == 256 and evidence["parity_pass_a"] is True):
        errors.append("REPLAY_A_NOT_256_PASS")

    if not (evidence["state_count_b"] == 256 and evidence["parity_pass_b"] is True):
        errors.append("REPLAY_B_NOT_256_PASS")

    admitted = not errors
    return {
        "verdict": "PASS_RUNTIME_ADMISSION" if admitted else "HOLD_RUNTIME_ADMISSION",
        "runtime_admission": admitted,
        "errors": errors,
    }
