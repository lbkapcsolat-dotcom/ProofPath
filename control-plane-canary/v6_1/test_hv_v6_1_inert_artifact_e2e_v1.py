#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORKER = BASE / "hv_v6_1_restart_worker_v1.py"


class HVInertArtifactE2EV1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "hv_runtime.sqlite3"
        self.artifact = self.root / "agent_memory.json"
        self.payload = {
            "schema": "HV_V6_1_INERT_AGENT_ARTIFACT_V1",
            "kind": "DATA_ONLY",
            "marker": "HORIZONTAL_ONLY_DO_NOT_PROMOTE",
            "payload": {
                "text": "attempt_horizontal_mint_v",
                "authority": "NONE",
            },
        }
        self.raw = json.dumps(self.payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.artifact.write_bytes(self.raw)
        self.sha256 = hashlib.sha256(self.raw).hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def run_fresh_worker(self):
        cp = subprocess.run(
            [
                sys.executable,
                str(WORKER),
                "artifact-mint",
                "--db",
                str(self.db),
                "--artifact",
                str(self.artifact),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "{}"
        return cp, json.loads(line)

    def test_01_write_close_reopen_preserves_exact_artifact_bytes(self):
        self.assertEqual(self.artifact.read_bytes(), self.raw)
        self.assertEqual(hashlib.sha256(self.artifact.read_bytes()).hexdigest(), self.sha256)

    def test_02_fresh_process_autoload_keeps_marker_inert_and_rejects_h_to_v_mint(self):
        cp, out = self.run_fresh_worker()
        self.assertEqual(cp.returncode, 0, msg=cp.stderr or cp.stdout)
        self.assertTrue(out["fresh_process_autoload"])
        self.assertTrue(out["inert_data_preserved"])
        self.assertEqual(out["artifact_sha256"], self.sha256)
        self.assertEqual(out["artifact_schema"], "HV_V6_1_INERT_AGENT_ARTIFACT_V1")
        self.assertEqual(out["marker"], "HORIZONTAL_ONLY_DO_NOT_PROMOTE")
        self.assertFalse(out["authority_minted"])
        self.assertFalse(out["executable"])
        self.assertEqual(out["obligation"], "OBL-17")
        self.assertEqual(out["verdict"], "REJECT_H_ONLY_CANNOT_MINT_V")

    def test_03_malicious_looking_text_remains_data_after_restart(self):
        cp, out = self.run_fresh_worker()
        self.assertEqual(cp.returncode, 0, msg=cp.stderr or cp.stdout)
        self.assertEqual(out["payload_text"], "attempt_horizontal_mint_v")
        self.assertEqual(out["payload_authority"], "NONE")
        self.assertFalse(out["authority_minted"])
        self.assertFalse(out["executable"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
