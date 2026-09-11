import json
import unittest
from pathlib import Path

from executor_binding import plan_execution, validate_execution_trace, ExecutorBindingError


ROOT = Path(__file__).resolve().parent
PROFILE = json.loads((ROOT / "ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json").read_text())
POLICY = json.loads((ROOT / "policy.json").read_text())


ROUTABLE = [
    ("model_hub", "search", "hugging-face", "hub_repo_search", "gateway-profile", {"query": "formal theorem proving Lean"}),
    ("papers", "search", "paper-search", "search_arxiv", "gateway-profile", {"query": "higher category theory homotopy theory"}),
    ("library_docs", "resolve", "context7", "resolve-library-id", "gateway-profile", {"query": "Docker Compose healthcheck", "libraryName": "Docker"}),
    ("astro_docs", "search", "astro-docs", "search_astro_docs", "gateway-profile", {"query": "content collections"}),
    ("docker_docs", "read", "docker-docs", "fetch_docker_docs", "gateway-profile", {}),
    ("java_docs", "search", "javadocs", "search_artifacts", "gateway-profile", {"query": "org.junit.jupiter"}),
    ("maven_metadata", "lookup", "maven-tools-mcp", "get_latest_version", "gateway-profile", {"dependency": "org.junit.jupiter:junit-jupiter"}),
    ("ros2_interfaces", "list", "ros2", "ros2_interface_list", "gateway-profile", {}),
    ("aws_cdk_guidance", "guidance", "aws-cdk-mcp-server", "CDKGeneralGuidance", "gateway-profile", {}),
    ("aws_terraform_docs", "search", "aws-terraform", "SearchAwsProviderDocs", "gateway-profile", {"asset_name": "aws_s3_bucket"}),
    ("openapi_schema", "list", "openapi-schema", "list-endpoints", "direct-image", {"openapiSchemaPath": "/schema.yaml"}),
    ("filesystem_readonly", "list", "rust-mcp-filesystem", "list_directory", "direct-image", {"path": "/data"}),
]


class RouterExecutorBindingTests(unittest.TestCase):
    def test_all_12_routable_surfaces_bind_exactly_to_executor_contract(self):
        seen = set()
        for domain, intent, surface, tool, transport, arguments in ROUTABLE:
            request = {"domain": domain, "intent": intent, "arguments": arguments}
            plan = plan_execution(request, PROFILE, POLICY)
            self.assertTrue(plan["executor_allowed"], plan)
            contract = plan["executor_contract"]
            self.assertEqual(surface, contract["surface"])
            self.assertEqual(tool, contract["tool"])
            self.assertEqual(transport, contract["transport"])
            self.assertEqual(arguments, contract["arguments"])
            self.assertTrue(contract["read_only"])
            self.assertFalse(contract["external_actuation"])
            trace = dict(contract)
            trace["executor_invoked"] = True
            validate_execution_trace(plan, trace)
            seen.add(surface)
        self.assertEqual(12, len(seen))
        self.assertNotIn("gemini-api-docs", seen)

    def test_direct_executor_projection_exactly_matches_canonical_contract(self):
        for domain, intent in [("openapi_schema", "list"), ("filesystem_readonly", "list")]:
            plan = plan_execution({"domain": domain, "intent": intent, "arguments": {}}, PROFILE, POLICY)
            contract = plan["executor_contract"]
            for field in ("surface", "tool", "transport", "arguments", "read_only", "external_actuation", "image_digest"):
                self.assertIn(field, plan)
                self.assertEqual(contract[field], plan[field])

    def test_negative_route_canaries_never_authorize_executor(self):
        cases = [
            ({"domain": "papers", "intent": "search", "requested_tool": "delete_paper"}, "WRONG_TOOL"),
            ({"domain": "papers", "intent": "search", "requested_transport": "direct-image"}, "TRANSPORT_MISMATCH"),
            ({"domain": "papers", "intent": "write"}, "FORBIDDEN_INTENT"),
            ({"domain": "gemini_api_docs", "intent": "read"}, "QUARANTINED_NONDETERMINISTIC_SURFACE"),
        ]
        for request, reason in cases:
            plan = plan_execution(request, PROFILE, POLICY)
            self.assertFalse(plan["executor_allowed"], plan)
            self.assertEqual("DENY", plan["route"]["decision"])
            self.assertEqual(reason, plan["route"]["reason"])
            self.assertNotIn("executor_contract", plan)

    def test_executor_trace_mismatch_fails_closed(self):
        plan = plan_execution({"domain": "papers", "intent": "search", "arguments": {"query": "x"}}, PROFILE, POLICY)
        good = dict(plan["executor_contract"])
        good["executor_invoked"] = True
        validate_execution_trace(plan, good)
        for field, bad in [("tool", "wrong"), ("transport", "direct-image"), ("surface", "context7")]:
            trace = dict(good)
            trace[field] = bad
            with self.assertRaises(ExecutorBindingError):
                validate_execution_trace(plan, trace)
        trace = dict(good)
        trace["arguments"] = {"query": "different"}
        with self.assertRaises(ExecutorBindingError):
            validate_execution_trace(plan, trace)


if __name__ == "__main__":
    unittest.main()
