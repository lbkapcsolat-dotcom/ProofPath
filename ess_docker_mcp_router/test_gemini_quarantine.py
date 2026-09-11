import unittest
from pathlib import Path

from router import load_profile, load_policy, route_request

ROOT = Path(__file__).resolve().parent


class GeminiQuarantineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(ROOT / "ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json")
        cls.policy = load_policy(ROOT / "policy.json")

    def test_gemini_get_current_model_is_quarantined_after_content_drift_proof(self):
        result = route_request(
            {"domain": "gemini_api_docs", "intent": "read"},
            self.profile,
            self.policy,
        )
        self.assertEqual("DENY", result["decision"])
        self.assertEqual("QUARANTINED_NONDETERMINISTIC_SURFACE", result["reason"])
        self.assertEqual(
            "ESS_DOCKER_MCP_GEMINI_API_DOCS_TRUE_CONTENT_DRIFT_SOURCE_PIN_AND_TEMPORAL_REPLAY_V1",
            result["quarantine_evidence_gate"],
        )
        self.assertTrue(result["read_only"])
        self.assertFalse(result["external_actuation"])


if __name__ == "__main__":
    unittest.main()
