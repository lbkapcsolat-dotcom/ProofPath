import unittest

from normalized_replay import normalize_gateway_receipt, normalized_receipts_equal


class NormalizedGatewayReplayTests(unittest.TestCase):
    def _base(self):
        return {
            "decision": "ALLOW",
            "reason": "ALLOW_MATCHED_ROUTE",
            "read_only": True,
            "external_actuation": False,
            "request_sha256": "req123",
            "route_sha256": "route123",
            "surface": "paper-search",
            "tool": "search_arxiv",
            "transport": "gateway-profile",
            "response_sha256": "resp123",
            "response": {"titles": ["A", "B"]},
            "runtime_meta": {
                "gateway_runtime_id": "runtime-a",
                "server_container_id": "container-a",
                "started_at": "2026-09-11T15:30:00Z",
            },
        }

    def test_ignores_only_runtime_metadata(self):
        first = self._base()
        second = self._base()
        second["runtime_meta"] = {
            "gateway_runtime_id": "runtime-b",
            "server_container_id": "container-b",
            "started_at": "2026-09-11T15:31:00Z",
        }
        self.assertEqual(normalize_gateway_receipt(first), normalize_gateway_receipt(second))
        self.assertTrue(normalized_receipts_equal(first, second))

    def test_detects_professional_response_change(self):
        first = self._base()
        second = self._base()
        second["response"] = {"titles": ["A", "C"]}
        second["response_sha256"] = "resp999"
        self.assertFalse(normalized_receipts_equal(first, second))


if __name__ == "__main__":
    unittest.main()
