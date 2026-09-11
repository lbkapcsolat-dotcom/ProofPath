import json
import unittest
from pathlib import Path

from router import load_profile, load_policy, route_request

ROOT = Path(__file__).resolve().parent


class RouterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(ROOT / "ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json")
        cls.policy = load_policy(ROOT / "policy.json")

    def test_authority_cardinality_is_exactly_13_unique_surfaces_with_12_routable_domains(self):
        surfaces = self.profile["surfaces"]
        names = [s["name"] for s in surfaces]
        quarantined = set(self.policy.get("quarantined_domains", {}))
        self.assertEqual(13, self.profile["surface_count"])
        self.assertEqual(13, len(surfaces))
        self.assertEqual(13, len(set(names)))
        self.assertEqual(13, len(self.policy["routes"]))
        self.assertEqual({"gemini_api_docs"}, quarantined)
        self.assertEqual(12, len(self.policy["routes"]) - len(quarantined))

    def test_policy_routes_bind_to_authority_and_quarantine_is_fail_closed(self):
        by_name = {s["name"]: s for s in self.profile["surfaces"]}
        quarantined = self.policy.get("quarantined_domains", {})
        for domain, expected in self.policy["routes"].items():
            with self.subTest(domain=domain):
                authoritative = by_name[expected["surface"]]
                self.assertEqual(authoritative["tool"], expected["tool"])
                self.assertEqual(authoritative["transport"], expected["transport"])
                result = route_request({"domain": domain, "intent": "read"}, self.profile, self.policy)
                if domain in quarantined:
                    self.assertEqual("DENY", result["decision"])
                    self.assertEqual("QUARANTINED_NONDETERMINISTIC_SURFACE", result["reason"])
                    self.assertEqual(quarantined[domain]["evidence_gate"], result["quarantine_evidence_gate"])
                    continue
                self.assertEqual("ALLOW", result["decision"])
                self.assertEqual(expected["surface"], result["surface"])
                self.assertEqual(expected["tool"], result["tool"])
                self.assertEqual(expected["transport"], result["transport"])
                self.assertTrue(result["read_only"])
                self.assertFalse(result["external_actuation"])

    def test_write_intent_is_fail_closed(self):
        result = route_request({"domain":"docker_docs","intent":"write"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("FORBIDDEN_INTENT", result["reason"])

    def test_unknown_domain_is_fail_closed(self):
        result = route_request({"domain":"totally_unknown","intent":"read"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("UNKNOWN_DOMAIN", result["reason"])

    def test_wrong_surface_is_fail_closed(self):
        result = route_request({"domain":"docker_docs","intent":"read","requested_surface":"aws-terraform"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("WRONG_ROUTE", result["reason"])

    def test_wrong_tool_is_fail_closed(self):
        result = route_request({"domain":"docker_docs","intent":"read","requested_tool":"deploy_stack"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("WRONG_TOOL", result["reason"])

    def test_direct_image_surface_cannot_be_forced_through_gateway(self):
        result = route_request({"domain":"openapi_schema","intent":"inspect","requested_transport":"gateway-profile"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("TRANSPORT_MISMATCH", result["reason"])

    def test_gateway_surface_cannot_be_forced_to_direct_image(self):
        result = route_request({"domain":"papers","intent":"search","requested_transport":"direct-image"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("TRANSPORT_MISMATCH", result["reason"])

    def test_hold_surfaces_are_not_routable(self):
        for surface in ["atlas-docs", "cloudflare-docs"]:
            with self.subTest(surface=surface):
                result = route_request({"domain":"docker_docs","intent":"read","requested_surface":surface}, self.profile, self.policy)
                self.assertEqual("DENY", result["decision"])

    def test_unknown_intent_is_denied(self):
        result = route_request({"domain":"papers","intent":"execute"}, self.profile, self.policy)
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("INTENT_NOT_ALLOWLISTED", result["reason"])


if __name__ == "__main__":
    unittest.main()
