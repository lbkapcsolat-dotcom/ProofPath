"""Fixture-driven execution of isolated deterministic canaries."""

from __future__ import annotations

from alpha6d.engine import execute_module
from alpha6d.envelope import make_object_envelope
from alpha6d.receipt import make_receipt, receipt_sha256


def run_canary(case: dict) -> dict:
    module = case["module"]
    policy = case.get("policy", {})
    evaluated_at = case["evaluated_at"]
    envelope = make_object_envelope(
        object_id=case["name"],
        object_type="task",
        payload=case["input"],
        policy_obj=policy,
        evaluated_at=evaluated_at,
    )
    output = execute_module(module, envelope)
    receipt = make_receipt(
        module_id=module,
        module_version="V1",
        input_obj=envelope,
        output_obj=output,
        verdict=output["verdict"],
        reason_code=output["reason_code"],
        policy_obj=policy,
        evaluated_at=evaluated_at,
    )
    return {
        "name": case["name"],
        "module": module,
        "output": output,
        "receipt": receipt,
        "receipt_sha256": receipt_sha256(receipt),
    }


def run_suite(fixtures: list[dict]) -> list[dict]:
    return [run_canary(case) for case in fixtures]
