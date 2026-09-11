import copy
import unittest

from post_quarantine_matrix import build_post_quarantine_cross_host_matrix


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

ROUTES = {
    "model_hub": {"surface": "hugging-face"},
    "papers": {"surface": "paper-search"},
    "library_docs": {"surface": "context7"},
    "astro_docs": {"surface": "astro-docs"},
    "docker_docs": {"surface": "docker-docs"},
    "gemini_api_docs": {"surface": "gemini-api-docs"},
    "java_docs": {"surface": "javadocs"},
    "maven_metadata": {"surface": "maven-tools-mcp"},
    "ros2_interfaces": {"surface": "ros2"},
    "aws_cdk_guidance": {"surface": "aws-cdk-mcp-server"},
    "aws_terraform_docs": {"surface": "aws-terraform"},
    "openapi_schema": {"surface": "openapi-schema"},
    "filesystem_readonly": {"surface": "rust-mcp-filesystem"},
}


def profile():
    return {"surface_count": 13, "surfaces": [{"name": n, "transport": t} for n, t in SURFACES]}


def policy():
    return {
        "routes": ROUTES,
        "quarantined_domains": {
            "gemini_api_docs": {
                "surface": "gemini-api-docs",
                "reason": "NONDETERMINISTIC_CONTENT_SELECTION",
            }
        },
    }


def host(label):
    results = {}
    for n, t in SURFACES:
        if n == "gemini-api-docs":
            continue
        response = f"stable-response-{n}\n"
        results[n] = {
            "surface": n,
            "transport": t,
            "status": "LIVE_PASS",
            "request_sha256": f"req-{n}",
            "route_sha256": f"route-{n}",
            "response": response,
            "response_sha256": f"resp-{n}",
        }
    return {
        "identity": {
            "boot_id": f"boot-{label}",
            "product_uuid": f"uuid-{label}",
            "runner_name": f"runner-{label}",
        },
        "results": results,
    }


class PostQuarantineMatrixTests(unittest.TestCase):
    def test_exact_12_routable_surfaces_pass_and_gemini_is_excluded(self):
        summary = build_post_quarantine_cross_host_matrix(profile(), policy(), host("a"), host("b"))
        self.assertEqual(13, summary["authority_surface_count"])
        self.assertEqual(12, summary["routable_surface_count"])
        self.assertEqual(12, summary["effective_invariant_count"])
        self.assertTrue(summary["all_routable_surfaces_invariant"])
        self.assertNotIn("gemini-api-docs", [r["surface"] for r in summary["rows"]])
        self.assertEqual(["gemini-api-docs"], summary["quarantined_surfaces"])

    def test_true_professional_drift_still_fails_closed(self):
        a, b = host("a"), host("b")
        b = copy.deepcopy(b)
        b["results"]["docker-docs"]["response"] = "DIFFERENT PROFESSIONAL CONTENT\n"
        summary = build_post_quarantine_cross_host_matrix(profile(), policy(), a, b)
        self.assertFalse(summary["all_routable_surfaces_invariant"])
        row = next(r for r in summary["rows"] if r["surface"] == "docker-docs")
        self.assertEqual("TRUE_CONTENT_DRIFT_HOLD", row["status"])


if __name__ == "__main__":
    unittest.main()
