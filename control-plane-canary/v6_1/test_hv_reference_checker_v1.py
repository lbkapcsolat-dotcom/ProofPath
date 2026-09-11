#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from hv_reference_checker_v1 import (
    EXPECTED_WOLFRAM_RECEIPT_BYTES,
    EXPECTED_WOLFRAM_RECEIPT_SHA256,
    build_conformance_receipt,
    canonical_json_bytes,
    find_guard_removal_countermodels,
    verify_obligations,
    verify_wolfram_receipt,
)

HERE = Path(__file__).resolve().parent
FORMAL_RECEIPT = HERE / "hv_formal_proof_receipt_v1.json"


class HVReferenceCheckerConformanceV1(unittest.TestCase):
    def test_01_wolfram_receipt_exact_binding(self):
        result = verify_wolfram_receipt(FORMAL_RECEIPT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["canonical_bytes"], EXPECTED_WOLFRAM_RECEIPT_BYTES)
        self.assertEqual(result["canonical_sha256"], EXPECTED_WOLFRAM_RECEIPT_SHA256)

    def test_02_all_18_obligations_hold_exhaustively(self):
        results = verify_obligations()
        self.assertEqual(set(results), {f"OBL-{i:02d}" for i in range(1, 19)})
        self.assertTrue(all(item["status"] == "PASS_EXHAUSTIVE_FINITE" for item in results.values()))
        self.assertTrue(all(item["counterexample"] is None for item in results.values()))

    def test_03_each_guard_removal_has_a_countermodel(self):
        countermodels = find_guard_removal_countermodels()
        self.assertEqual(set(countermodels), {f"OBL-{i:02d}" for i in range(1, 19)})
        self.assertTrue(all(countermodels[key] is not None for key in countermodels))

    def test_04_conformance_receipt_is_deterministic(self):
        a = build_conformance_receipt(FORMAL_RECEIPT)
        b = build_conformance_receipt(FORMAL_RECEIPT)
        self.assertEqual(canonical_json_bytes(a), canonical_json_bytes(b))
        self.assertEqual(a["verdict"], "PASS_HV_REFERENCE_CHECKER_CONFORMANCE_18_OF_18")
        self.assertEqual(a["obligations_passed"], 18)
        self.assertEqual(a["guard_removal_countermodels_found"], 18)
        self.assertEqual(a["formal_receipt_sha256"], EXPECTED_WOLFRAM_RECEIPT_SHA256)
        self.assertFalse(a["claims"]["general_theorem"])
        self.assertFalse(a["claims"]["runtime_admission"])
        self.assertFalse(a["claims"]["production_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
