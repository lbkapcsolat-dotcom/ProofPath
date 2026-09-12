import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import Tri, check_semantic_crosswalk, load_namespace

IDENTITY = tuple(range(6))
PASS11 = {f"C{i}": "PASS" for i in range(1, 12)}
HOLD11 = {f"C{i}": "HOLD" for i in range(1, 12)}
FULL_EQ = [{"source": i, "target": i, "evidence_id": f"E-{i}"} for i in range(6)]


class SemanticGateTests(unittest.TestCase):
    def setUp(self):
        self.ess = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        self.aip = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")

    def full_evidence(self):
        return {"criteria": dict(PASS11), "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}

    def test_real_namespaces_without_semantic_evidence_hold(self):
        evidence = {"criteria": dict(HOLD11), "axis_equivalences": [], "exact_mapping": None}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)
        self.assertIn("NO_AXIS_LEVEL_EVIDENCE", result["reason_codes"])

    def test_five_of_six_axis_evidence_holds(self):
        evidence = {"criteria": dict(PASS11), "axis_equivalences": FULL_EQ[:5], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)

    def test_polarity_conflict_denies(self):
        criteria = dict(PASS11)
        criteria["C4"] = "DENY"
        evidence = {"criteria": criteria, "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("POLARITY_CONFLICT", result["reason_codes"])

    def test_alias_conflict_denies(self):
        criteria = dict(PASS11)
        criteria["C5"] = "DENY"
        evidence = {"criteria": criteria, "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)

    def test_post_hoc_selection_denies(self):
        criteria = dict(PASS11)
        criteria["C9"] = "DENY"
        evidence = {"criteria": criteria, "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)

    def test_bare_eq64_denies_by_policy(self):
        bare = dict(self.aip)
        bare["namespace_id"] = "EQ64"
        result = check_semantic_crosswalk(bare, self.ess, self.full_evidence(), IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("DENY_POLICY_BARE_EQ64_FORBIDDEN", result["reason_codes"])

    def test_unknown_namespace_holds(self):
        unknown = dict(self.aip)
        unknown["namespace_id"] = "UNKNOWN_NAMESPACE"
        result = check_semantic_crosswalk(unknown, self.ess, self.full_evidence(), IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)
        self.assertIn("UNREGISTERED_NAMESPACE", result["reason_codes"])

    def assert_registered_schema_mutation_denied(self, mutated):
        result = check_semantic_crosswalk(mutated, self.ess, self.full_evidence(), IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("REGISTERED_NAMESPACE_SCHEMA_MISMATCH", result["reason_codes"])

    def test_registered_namespace_mutated_axes_denies(self):
        mutated = dict(self.aip)
        mutated["axes"] = list(self.aip["axes"])
        mutated["axes"][0] = "Authority_MUTATED"
        self.assert_registered_schema_mutation_denied(mutated)

    def test_registered_namespace_mutated_polarity_denies(self):
        mutated = dict(self.aip)
        mutated["polarity"] = list(self.aip["polarity"])
        mutated["polarity"][0] = "neutral"
        self.assert_registered_schema_mutation_denied(mutated)

    def test_registered_namespace_mutated_structural_class_denies(self):
        mutated = dict(self.aip)
        mutated["structural_class"] = "NOT_B6_Q6"
        self.assert_registered_schema_mutation_denied(mutated)

    def test_registered_namespace_mutated_claim_ceiling_denies(self):
        mutated = dict(self.aip)
        mutated["claim_ceiling"] = "MUTATED_CEILING"
        self.assert_registered_schema_mutation_denied(mutated)


if __name__ == "__main__":
    unittest.main()
