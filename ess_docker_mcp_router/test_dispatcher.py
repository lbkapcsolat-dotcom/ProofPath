import unittest

from dispatcher import dispatch_request, receipts_equal
from router import load_policy, load_profile

PROFILE = "ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json"
POLICY = "policy.json"


class DispatcherContractTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(PROFILE)
        self.policy = load_policy(POLICY)

    def test_allowed_request_dispatches_once_and_builds_deterministic_receipt(self):
        calls = []

        def executor(route, arguments):
            calls.append((route, arguments))
            return {"endpoints": ["GET /health"], "ok": True}

        request = {
            "domain": "openapi_schema",
            "intent": "list",
            "requested_surface": "openapi-schema",
            "requested_tool": "list-endpoints",
            "requested_transport": "direct-image",
            "arguments": {"openapiSchemaPath": "/evidence/synthetic-openapi.yaml"},
        }
        first = dispatch_request(request, self.profile, self.policy, executor)
        second = dispatch_request(request, self.profile, self.policy, executor)

        self.assertEqual(2, len(calls))
        self.assertEqual("ALLOW", first["decision"])
        self.assertEqual("openapi-schema", first["surface"])
        self.assertEqual("list-endpoints", first["tool"])
        self.assertEqual("direct-image", first["transport"])
        self.assertTrue(first["read_only"])
        self.assertFalse(first["external_actuation"])
        self.assertEqual(first["request_sha256"], second["request_sha256"])
        self.assertEqual(first["route_sha256"], second["route_sha256"])
        self.assertEqual(first["response_sha256"], second["response_sha256"])
        self.assertTrue(receipts_equal(first, second))

    def test_denied_request_never_calls_executor(self):
        called = False

        def executor(route, arguments):
            nonlocal called
            called = True
            return {"unexpected": True}

        request = {"domain": "openapi_schema", "intent": "write"}
        receipt = dispatch_request(request, self.profile, self.policy, executor)

        self.assertFalse(called)
        self.assertEqual("DENY", receipt["decision"])
        self.assertEqual("FORBIDDEN_INTENT", receipt["reason"])
        self.assertNotIn("response_sha256", receipt)
        self.assertTrue(receipt["read_only"])
        self.assertFalse(receipt["external_actuation"])


if __name__ == "__main__":
    unittest.main()
