from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNNER = ROOT / "hgraph_adapter" / "run_shadow_receipt.py"
VERIFIER = ROOT / "hgraph_adapter" / "verify_shadow_receipt.py"


class XB18ReceiptProcessTests(unittest.TestCase):
    def test_runner_then_independent_verifier_process(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = pathlib.Path(td) / "package"
            run = subprocess.run(
                [sys.executable, str(RUNNER), "--output-dir", str(output_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr or run.stdout)
            for name in (
                "request.json",
                "verdict.json",
                "receipt.json",
                "shadow_canary_summary.json",
            ):
                self.assertTrue((output_dir / name).is_file(), name)

            receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["semantic_status"], "HOLD")
            self.assertEqual(receipt["claim_ceiling"], "STRUCTURAL_ONLY")
            self.assertFalse(receipt["runtime_bind"])

            summary = json.loads(
                (output_dir / "shadow_canary_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["schema"], "HGRAPH_XB18_REAL_SHADOW_CANARY_SUMMARY_V1")
            self.assertEqual(summary["source_namespace"], "X_AIPRBG_6GATE_DIAGNOSTIC_V1")
            self.assertEqual(summary["target_namespace"], "ESS_EQ64_6D_KERNEL")
            self.assertEqual(summary["structural_status"], "PASS")
            self.assertEqual(summary["semantic_status"], "HOLD")
            self.assertEqual(summary["claim_ceiling"], "STRUCTURAL_ONLY")
            self.assertEqual(summary["reason_codes"], ["NO_AXIS_LEVEL_EVIDENCE"])
            self.assertFalse(summary["runtime_bind"])
            self.assertEqual(summary["receipt_payload_sha256"], receipt["payload_sha256"])

            verify = subprocess.run(
                [sys.executable, str(VERIFIER), "--package-dir", str(output_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr or verify.stdout)
            self.assertIn("PASS_XB18_INDEPENDENT_RECEIPT_READBACK", verify.stdout)
            self.assertIn("PASS_XB18_REAL_SHADOW_CANARY_SUMMARY", verify.stdout)


if __name__ == "__main__":
    unittest.main()
