import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary
from receipt import build_receipt, readback_receipt, write_canonical_json, write_receipt

HOLD11 = {f"C{i}": "HOLD" for i in range(1, 12)}


class Canary720Tests(unittest.TestCase):
    def real_inputs(self):
        source_path = ROOT / "fixtures" / "x_aiprbg_6gate.json"
        target_path = ROOT / "fixtures" / "ess_eq64_6d_kernel.json"
        source = load_namespace(source_path)
        target = load_namespace(target_path)
        evidence = {"criteria": dict(HOLD11), "axis_equivalences": [], "exact_mapping": None}
        return source_path, target_path, source, target, evidence

    def test_real_namespaces_have_zero_semantic_leakage(self):
        _, _, source, target, evidence = self.real_inputs()
        result = run_canary(source, target, evidence)
        self.assertEqual(result["permutation_count"], 720)
        self.assertEqual(result["structural_pass"], 720)
        self.assertEqual(result["semantic_pass"], 0)
        self.assertEqual(result["semantic_hold"], 720)
        self.assertEqual(result["semantic_deny"], 0)
        self.assertEqual(result["semantic_pass_permutations"], [])
        self.assertEqual(len(result["results"]), 720)

    def test_real_receipt_roundtrip_binds_all_inputs(self):
        source_path, target_path, source, target, evidence = self.real_inputs()
        result = run_canary(source, target, evidence)
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            evidence_path = td / "evidence.json"
            result_path = td / "result.json"
            receipt_path = td / "receipt.json"
            write_canonical_json(evidence_path, evidence)
            write_canonical_json(result_path, result)
            receipt = build_receipt(ROOT, source_path, target_path, evidence_path, result_path)
            write_receipt(receipt_path, receipt)
            reread = readback_receipt(receipt_path)
        self.assertEqual(reread, receipt)
        self.assertEqual(receipt["run_kind"], "NEGATIVE_CANARY")
        self.assertEqual(receipt["gate_status"], "PASS")
        self.assertEqual(receipt["unexpected_passes"], [])
        self.assertFalse(receipt["runtime_bind"])

    def test_negative_canary_receipt_rejects_nonpassing_summaries(self):
        source_path, target_path, source, target, evidence = self.real_inputs()
        result = run_canary(source, target, evidence)
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            evidence_path = td / "evidence.json"
            result_path = td / "result.json"
            receipt_path = td / "receipt.json"
            write_canonical_json(evidence_path, evidence)
            write_canonical_json(result_path, result)
            receipt = build_receipt(ROOT, source_path, target_path, evidence_path, result_path)

            mutations = []
            bad_structural = dict(receipt)
            bad_structural["structural_pass"] = 719
            mutations.append(bad_structural)

            bad_semantic = dict(receipt)
            bad_semantic["semantic_pass"] = 1
            bad_semantic["semantic_hold"] = 719
            mutations.append(bad_semantic)

            bad_unexpected = dict(receipt)
            bad_unexpected["unexpected_passes"] = [[0, 1, 2, 3, 4, 5]]
            mutations.append(bad_unexpected)

            for mutated in mutations:
                with self.subTest(mutated=mutated):
                    with self.assertRaises(ValueError):
                        write_receipt(receipt_path, mutated)


if __name__ == "__main__":
    unittest.main()
