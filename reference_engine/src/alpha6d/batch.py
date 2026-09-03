"""Independent-job batch aggregation."""

from __future__ import annotations

import hashlib

from alpha6d.contracts import verdict_hold, verdict_pass


def job_key(input_identity: str, contract_fingerprint: str, policy_fingerprint: str) -> str:
    payload = (input_identity + contract_fingerprint + policy_fingerprint).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate_batch(case: dict) -> dict:
    jobs = case.get("jobs", [])
    required = [job for job in jobs if job.get("required", False) is True]
    total = len(required)
    explicit_ids = [job.get("job_id") for job in jobs if job.get("job_id") is not None]
    if len(explicit_ids) != len(set(explicit_ids)):
        return {
            **verdict_hold("HOLD_IDENTITY"),
            "batch_status": f"HOLD_0_OF_{total}",
            "required_passed": 0,
            "required_total": total,
        }
    passed = sum(1 for job in required if job.get("verdict") == "PASS")
    all_pass = total > 0 and passed == total
    prefix = "PASS" if all_pass else "HOLD"
    status = f"{prefix}_{passed}_OF_{total}"
    if all_pass:
        return {**verdict_pass(), "batch_status": status, "required_passed": passed, "required_total": total}
    return {
        **verdict_hold("HOLD_PRECONDITION", "G8_PRECONDITION"),
        "batch_status": status,
        "required_passed": passed,
        "required_total": total,
    }
