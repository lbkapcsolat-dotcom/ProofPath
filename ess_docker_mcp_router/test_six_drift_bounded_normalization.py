import json
import unittest

from drift_normalization import canonicalize_surface_response, diagnose_pair


class SixDriftBoundedNormalizationTests(unittest.TestCase):
    def test_timing_prefix_only_surfaces_are_equal_after_bounded_strip(self):
        for surface in ("hugging-face", "astro-docs", "javadocs"):
            a = "Tool call took: 293.102133ms\nPAYLOAD\n"
            b = "Tool call took: 1.83s\nPAYLOAD\n"
            self.assertEqual(canonicalize_surface_response(surface, a), canonicalize_surface_response(surface, b))
            self.assertEqual(diagnose_pair(surface, a, b)["classification"], "BOUNDED_TIMING_NOISE")
            c = "Tool call took: 1.83s\nCHANGED\n"
            self.assertNotEqual(canonicalize_surface_response(surface, a), canonicalize_surface_response(surface, c))

    def test_context7_record_order_is_bounded_but_record_content_is_not(self):
        a = "- Title: A\n- ID: /a\n----------\n- Title: B\n- ID: /b\n"
        b = "- Title: B\n- ID: /b\n----------\n- Title: A\n- ID: /a\n"
        self.assertEqual(canonicalize_surface_response("context7", a), canonicalize_surface_response("context7", b))
        self.assertEqual(diagnose_pair("context7", a, b)["classification"], "BOUNDED_RECORD_ORDER_NOISE")
        c = b.replace("/a", "/changed")
        self.assertNotEqual(canonicalize_surface_response("context7", a), canonicalize_surface_response("context7", c))

    def test_ros2_json_list_order_is_bounded_but_membership_is_not(self):
        a = json.dumps(["pkg/msg/B", "pkg/msg/A"])
        b = json.dumps(["pkg/msg/A", "pkg/msg/B"])
        self.assertEqual(canonicalize_surface_response("ros2", a), canonicalize_surface_response("ros2", b))
        self.assertEqual(diagnose_pair("ros2", a, b)["classification"], "BOUNDED_LIST_ORDER_NOISE")
        c = json.dumps(["pkg/msg/A", "pkg/msg/C"])
        self.assertNotEqual(canonicalize_surface_response("ros2", a), canonicalize_surface_response("ros2", c))

    def test_gemini_content_drift_is_never_normalized_away(self):
        a = "## gemini-2.0-flash\nold model page\n"
        b = "## Gemini 3\ncurrent model catalog\n"
        self.assertNotEqual(canonicalize_surface_response("gemini-api-docs", a), canonicalize_surface_response("gemini-api-docs", b))
        self.assertEqual(diagnose_pair("gemini-api-docs", a, b)["classification"], "TRUE_CONTENT_DRIFT")


if __name__ == "__main__":
    unittest.main()
