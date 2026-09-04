from alpha6d.receipt import make_receipt, receipt_bytes, receipt_sha256


def make(output):
    return make_receipt(
        module_id="GAP_ENGINE",
        module_version="V1",
        input_obj={"x": 1},
        output_obj=output,
        verdict="PASS",
        reason_code="PASS",
        policy_obj={"max_cost": 0},
        evaluated_at="2026-09-01T12:00:00Z",
    )


def test_identical_receipts_have_identical_bytes_and_hashes():
    a = make({"severity_bp": 4320})
    b = make({"severity_bp": 4320})
    assert receipt_bytes(a) == receipt_bytes(b)
    assert receipt_sha256(a) == receipt_sha256(b)


def test_changed_output_changes_receipt_hash():
    a = make({"severity_bp": 4320})
    b = make({"severity_bp": 4321})
    assert receipt_sha256(a) != receipt_sha256(b)
