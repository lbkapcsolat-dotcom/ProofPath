import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary

PASS11 = {f"C{i}": "PASS" for i in range(1, 12)}
IDENTITY = [0, 1, 2, 3, 4, 5]
FULL_EQ = [
    {"source": i, "target": i, "evidence_id": f"SYN-{i}"} for i in range(6)
]


class PositiveControlTests(unittest.TestCase):
    def test_exactly_one_predeclared_mapping_passes(self):
        source = load_namespace(ROOT / "fixtures" / "synthetic_exact_a.json")
        target = load_namespace(ROOT / "fixtures" / "synthetic_exact_b.json")
        evidence = {
            "criteria": dict(PASS11),
            "axis_equivalences": FULL_EQ,
            "exact_mapping": IDENTITY,
        }
        result = run_canary(source, target, evidence)
        self.assertEqual(result["permutation_count"], 720)
        self.assertEqual(result["structural_pass"], 720)
        self.assertEqual(result["semantic_pass"], 1)
        self.assertEqual(result["semantic_hold"], 0)
        self.assertEqual(result["semantic_deny"], 719)
        self.assertEqual(result["semantic_pass_permutations"], [IDENTITY])


if __name__ == "__main__":
    unittest.main()
