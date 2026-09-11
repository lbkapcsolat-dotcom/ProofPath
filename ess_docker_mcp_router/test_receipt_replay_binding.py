import copy
import json
import unittest
from pathlib import Path

from executor_binding import plan_execution
from receipt_binding import (
    ReceiptBindingError,
    build_surface_receipt,
    compare_independent_replay,
    validate_surface_receipt,
)


ROOT = Path(__file__).resolve().parent
PROFILE = json.loads((ROOT / "ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json").read_text())
POLICY = json.loads((ROOT / "policy.json").read_text())
POLICY_SHA = "a" * 64
PROFILE_SHA = "b" * 64


def make_bound(domain, intent, arguments, response, execution_id):
    request = {"domain": domain, "intent": intent, "arguments": arguments}
    plan = plan_execution(request, PROFILE, POLICY)
    assert plan["executor_allowed"]
    trace = dict(plan["executor_contract"])
    trace.update({"executor_invoked": True, "exit_code": 0})
    receipt = build_surface_receipt(
        request=request,
        plan=plan,
        trace=trace,
        response_bytes=response,
        policy_sha256=POLICY_SHA,
        profile_sha256=PROFILE_SHA,
        execution_id=execution_id,
    )
    return request, plan, trace, receipt


class ReceiptReplayBindingTests(unittest.TestCase):
    def test_receipt_binds_request_route_executor_trace_response_and_authority(self):
        request, plan, trace, receipt = make_bound(
            "papers", "search", {"query": "higher category theory"}, b"primary-response", "primary-papers"
        )
        result = validate_surface_receipt(
            receipt=receipt,
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=b"primary-response",
            policy_sha256=POLICY_SHA,
            profile_sha256=PROFILE_SHA,
        )
        self.assertTrue(result["receipt_valid"])
        self.assertEqual("paper-search", receipt["surface"])
        self.assertEqual("gateway-profile", receipt["transport"])
        self.assertTrue(receipt["response_nonempty"])
        self.assertEqual(16, receipt["response_bytes"])
        self.assertTrue(receipt["receipt_sha256"])

    def test_receipt_tamper_canaries_fail_closed(self):
        request, plan, trace, receipt = make_bound(
            "papers", "search", {"query": "x"}, b"response", "primary-tamper"
        )
        cases = []
        r = copy.deepcopy(receipt); r["route_sha256"] = "0" * 64; cases.append(r)
        r = copy.deepcopy(receipt); r["executor_contract_sha256"] = "1" * 64; cases.append(r)
        r = copy.deepcopy(receipt); r["response_sha256"] = "2" * 64; cases.append(r)
        r = copy.deepcopy(receipt); r["request_sha256"] = "3" * 64; cases.append(r)
        r = copy.deepcopy(receipt); r["policy_sha256"] = "4" * 64; cases.append(r)
        r = copy.deepcopy(receipt); r["profile_sha256"] = "5" * 64; cases.append(r)
        for tampered in cases:
            with self.assertRaises(ReceiptBindingError):
                validate_surface_receipt(
                    receipt=tampered,
                    request=request,
                    plan=plan,
                    trace=trace,
                    response_bytes=b"response",
                    policy_sha256=POLICY_SHA,
                    profile_sha256=PROFILE_SHA,
                )

    def test_direct_image_replay_requires_exact_response_sha(self):
        _, _, _, primary = make_bound(
            "openapi_schema", "list", {"openapiSchemaPath": "/schema.yaml"}, b"same-response", "primary-openapi"
        )
        _, _, _, replay = make_bound(
            "openapi_schema", "list", {"openapiSchemaPath": "/schema.yaml"}, b"same-response", "replay-openapi"
        )
        result = compare_independent_replay(primary, replay)
        self.assertTrue(result["replay_valid"])
        self.assertTrue(result["response_sha256_equal"])
        self.assertEqual("EXACT_RESPONSE_REPLAY", result["response_equivalence"])

        _, _, _, changed = make_bound(
            "openapi_schema", "list", {"openapiSchemaPath": "/schema.yaml"}, b"different-response", "replay-openapi-2"
        )
        with self.assertRaises(ReceiptBindingError):
            compare_independent_replay(primary, changed)

    def test_gateway_replay_allows_remote_response_drift_but_not_binding_drift(self):
        _, _, _, primary = make_bound(
            "papers", "search", {"query": "x"}, b"remote-result-A", "primary-paper"
        )
        _, _, _, replay = make_bound(
            "papers", "search", {"query": "x"}, b"remote-result-B", "replay-paper"
        )
        result = compare_independent_replay(primary, replay)
        self.assertTrue(result["replay_valid"])
        self.assertFalse(result["response_sha256_equal"])
        self.assertEqual("RESPONSE_INDIVIDUALLY_BOUND__BYTE_EQUALITY_NOT_REQUIRED", result["response_equivalence"])

        other_request, other_plan, other_trace, other = make_bound(
            "library_docs", "resolve", {"query": "x", "libraryName": "Docker"}, b"remote-result-C", "replay-other"
        )
        self.assertIsNotNone(other_request)
        self.assertIsNotNone(other_plan)
        self.assertIsNotNone(other_trace)
        with self.assertRaises(ReceiptBindingError):
            compare_independent_replay(primary, other)

    def test_replay_must_be_distinct_execution_and_response_must_be_nonempty(self):
        _, _, _, primary = make_bound(
            "papers", "search", {"query": "x"}, b"response", "same-execution"
        )
        _, _, _, same_id = make_bound(
            "papers", "search", {"query": "x"}, b"response", "same-execution"
        )
        with self.assertRaises(ReceiptBindingError):
            compare_independent_replay(primary, same_id)

        request = {"domain": "papers", "intent": "search", "arguments": {"query": "x"}}
        plan = plan_execution(request, PROFILE, POLICY)
        trace = dict(plan["executor_contract"])
        trace.update({"executor_invoked": True, "exit_code": 0})
        with self.assertRaises(ReceiptBindingError):
            build_surface_receipt(
                request=request,
                plan=plan,
                trace=trace,
                response_bytes=b"",
                policy_sha256=POLICY_SHA,
                profile_sha256=PROFILE_SHA,
                execution_id="empty-response",
            )


if __name__ == "__main__":
    unittest.main()
