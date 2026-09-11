import copy
import unittest

from coverage_matrix import build_cross_host_coverage


SURFACES = [
    ("hugging-face", "gateway-profile"),
    ("paper-search", "gateway-profile"),
    ("context7", "gateway-profile"),
    ("astro-docs", "gateway-profile"),
    ("docker-docs", "gateway-profile"),
    ("gemini-api-docs", "gateway-profile"),
    ("javadocs", "gateway-profile"),
    ("maven-tools-mcp", "gateway-profile"),
    ("ros2", "gateway-profile"),
    ("aws-cdk-mcp-server", "gateway-profile"),
    ("aws-terraform", "gateway-profile"),
    ("openapi-schema", "direct-image"),
    ("rust-mcp-filesystem", "direct-image"),
]


def profile():
    return {"surfaces": [{"name": n, "transport": t} for n, t in SURFACES]}


def host(label, seed):
    return {
        "identity": {
            "host_label": label,
            "boot_id": f"boot-{label}",
            "product_uuid": f"uuid-{label}",
            "runner_name": f"runner-{label}",
        },
        "results": {
            n: {
                "surface": n,
                "transport": t,
                "request_sha256": f"req-{seed}-{n}",
                "route_sha256": f"route-{seed}-{n}",
                "response_sha256": f"resp-{seed}-{n}",
                "response": f"response-{seed}-{n}",
                "status": "LIVE_PASS",
            }
            for n, t in SURFACES
        },
    }


class CrossHost13SurfaceCoverageTests(unittest.TestCase):
    def test_full_exact_13_surface_dual_transport_equality_passes(self):
        a = host("a", "same")
        b = host("b", "same")
        summary = build_cross_host_coverage(profile(), a, b)
        self.assertEqual(summary["surface_count"], 13)
        self.assertEqual(summary["gateway_profile_count"], 11)
        self.assertEqual(summary["direct_image_count"], 2)
        self.assertEqual(summary["equal_surface_count"], 13)
        self.assertTrue(summary["all_surfaces_equal"])
        self.assertTrue(summary["distinct_host_identity"])

    def test_professional_response_drift_is_not_normalized_away(self):
        a = host("a", "same")
        b = host("b", "same")
        b = copy.deepcopy(b)
        b["results"]["context7"]["response"] = "DIFFERENT PROFESSIONAL CONTENT"
        b["results"]["context7"]["response_sha256"] = "different"
        summary = build_cross_host_coverage(profile(), a, b)
        self.assertFalse(summary["all_surfaces_equal"])
        row = next(r for r in summary["rows"] if r["surface"] == "context7")
        self.assertEqual(row["status"], "CROSS_HOST_CONTENT_DRIFT")


if __name__ == "__main__":
    unittest.main()
