import unittest

from drift_normalization import diagnose_pair


class MavenTimingNormalizationTests(unittest.TestCase):
    def test_maven_millisecond_timing_prefix_is_bounded_noise(self):
        professional = '{"status":"success","data":{"dependency":"org.junit.jupiter:junit-jupiter","latest_stable":{"version":"6.1.3","type":"stable"},"total_versions":87}}\n'
        with_timing = 'Tool call took: 819.718721ms\n' + professional
        result = diagnose_pair("maven-tools-mcp", professional, with_timing)
        self.assertEqual("BOUNDED_TIMING_NOISE", result["classification"])
        self.assertTrue(result["equal_after_bounded_normalization"])

    def test_maven_professional_change_is_not_hidden_by_timing_prefix(self):
        first = '{"status":"success","data":{"latest_stable":{"version":"6.1.3"}}}\n'
        second = 'Tool call took: 819.718721ms\n{"status":"success","data":{"latest_stable":{"version":"6.1.4"}}}\n'
        result = diagnose_pair("maven-tools-mcp", first, second)
        self.assertEqual("TRUE_CONTENT_DRIFT", result["classification"])
        self.assertFalse(result["equal_after_bounded_normalization"])


if __name__ == "__main__":
    unittest.main()
