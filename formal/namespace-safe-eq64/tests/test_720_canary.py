import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary

HOLD11 = {f"C{i}": "HOLD" for i in range(1, 12)}


class Canary720Tests(unittest.TestCase):
    def test_real_namespaces_have_zero_semantic_leakage(self):
        source = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")
        target = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        evidence = {"criteria": dict(HOLD11), "axis_equivalences": [], "exact_mapping": None}
        result = run_canary(source, target, evidence)
        self.assertEqual(result["permutation_count"], 720)
        self.assertEqual(result["structural_pass"], 720)
        self.assertEqual(result["semantic_pass"], 0)
        self.assertEqual(result["semantic_hold"], 720)
        self.assertEqual(result["semantic_deny"], 0)
        self.assertEqual(result["semantic_pass_permutations"], [])
        self.assertEqual(len(result["results"]), 720)


if __name__ == "__main__":
    unittest.main()
