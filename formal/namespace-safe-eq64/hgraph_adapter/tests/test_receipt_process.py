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
            for name in ("request.json", "verdict.json", "receipt.json"):
                self.assertTrue((output_dir / name).is_file(), name)

            receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["semantic_status"], "HOLD")
            self.assertEqual(receipt["claim_ceiling"], "STRUCTURAL_ONLY")
            self.assertFalse(receipt["runtime_bind"])

            verify = subprocess.run(
                [sys.executable, str(VERIFIER), "--package-dir", str(output_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr or verify.stdout)
            self.assertIn("PASS_XB18_INDEPENDENT_RECEIPT_READBACK", verify.stdout)


if __name__ == "__main__":
    unittest.main()
