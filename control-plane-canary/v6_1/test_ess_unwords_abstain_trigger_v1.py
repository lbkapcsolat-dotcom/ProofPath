import unittest

import alpha_full_6d_local_control_plane_v6_1 as v61


class UnwordsSemanticGate12CaseCanary(unittest.TestCase):
    def setUp(self):
        self.gate = v61.UnwordsSemanticGate()
        self.payload = b"raw_unwords_experience_01"
        self.labels = {"LOVE", "LOSS", "ANGER", "GRIEF"}

    def eval(self, proofs=None, conf=None, *, ood=0.1, complete=True, payload=None):
        return self.gate.evaluate_state(
            self.payload if payload is None else payload,
            self.labels,
            {} if proofs is None else proofs,
            {} if conf is None else conf,
            ood_score=ood,
            evidence_complete=complete,
        )

    def test_case_01_clean_classification(self):
        dec = self.eval({"ANGER": True}, {"LOVE": 0.95, "LOSS": 0.10, "GRIEF": 0.05})
        self.assertEqual((dec.state, dec.reason), ("CLASSIFIED", "LOVE"))

    def test_case_02_exhausted_label_space_abstains(self):
        dec = self.eval({label: True for label in self.labels}, {})
        self.assertEqual((dec.state, dec.reason), ("ABSTAIN", v61.AbstainReason.EXHAUSTED_LABEL_SPACE.value))

    def test_case_03_ambiguous_margin_abstains(self):
        dec = self.eval({"ANGER": True}, {"LOVE": 0.88, "LOSS": 0.85, "GRIEF": 0.10})
        self.assertEqual((dec.state, dec.reason), ("ABSTAIN", v61.AbstainReason.AMBIGUOUS_ADMISSIBLE_SET.value))

    def test_case_04_out_of_distribution_abstains(self):
        dec = self.eval({}, {"LOVE": 0.99}, ood=0.95)
        self.assertEqual((dec.state, dec.reason), ("ABSTAIN", v61.AbstainReason.OUT_OF_DISTRIBUTION.value))

    def test_case_05_low_confidence_abstains(self):
        dec = self.eval({}, {"LOVE": 0.79})
        self.assertEqual((dec.state, dec.reason), ("ABSTAIN", v61.AbstainReason.INSUFFICIENT_EVIDENCE.value))

    def test_case_06_unproven_rejection_is_blocked(self):
        with self.assertRaises(v61.MissingExclusionProofException):
            self.eval({"LOSS": False}, {"LOVE": 0.99})

    def test_case_07_incomplete_evidence_abstains_even_with_high_confidence(self):
        dec = self.eval({}, {"LOVE": 0.99}, complete=False)
        self.assertEqual((dec.state, dec.reason), ("ABSTAIN", v61.AbstainReason.INSUFFICIENT_EVIDENCE.value))

    def test_case_08_identical_input_produces_identical_receipt(self):
        a = self.eval({"ANGER": True}, {"LOVE": 0.95, "LOSS": 0.10, "GRIEF": 0.05})
        b = self.eval({"ANGER": True}, {"GRIEF": 0.05, "LOSS": 0.10, "LOVE": 0.95})
        self.assertEqual(a.receipt_hash, b.receipt_hash)
        self.assertRegex(a.receipt_hash, r"^[0-9a-f]{64}$")

    def test_case_09_payload_mutation_changes_receipt(self):
        a = self.eval({}, {"LOVE": 0.79}, payload=b"raw_unwords_experience_01")
        b = self.eval({}, {"LOVE": 0.79}, payload=b"raw_unwords_experience_02")
        self.assertNotEqual(a.receipt_hash, b.receipt_hash)

    def test_case_10_nan_ood_score_is_fail_closed(self):
        with self.assertRaises(v61.SemanticInputValidationException):
            self.eval({}, {"LOVE": 0.99}, ood=float("nan"))

    def test_case_11_nan_confidence_is_fail_closed(self):
        with self.assertRaises(v61.SemanticInputValidationException):
            self.eval({}, {"LOVE": float("nan")})

    def test_case_12_rejection_outside_ontology_is_fail_closed(self):
        with self.assertRaises(v61.SemanticInputValidationException):
            self.eval({"NOT_IN_LABEL_SPACE": True}, {"LOVE": 0.99})


if __name__ == "__main__":
    unittest.main(verbosity=2)
