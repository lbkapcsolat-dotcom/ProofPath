#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import run_canary


class CanaryTests(unittest.TestCase):
    def test_frozen_source_identity(self):
        self.assertEqual(run_canary.verify_frozen_source(), run_canary.FROZEN_SOURCE_SHA256)

    def test_positive_pass_and_nonce_tamper_reject(self):
        fixed = datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc)
        receipt = run_canary.run_bounded_canary(now=fixed)
        self.assertEqual(receipt["positive_result"]["verdict"], run_canary.PASS_VERDICT)
        self.assertEqual(receipt["positive_result"]["eq64_bits"], "111111")
        self.assertEqual(receipt["negative_result"]["verdict"], run_canary.EXPECTED_NEGATIVE_VERDICT)
        self.assertFalse(receipt["external_actuation"])
        self.assertFalse(receipt["production_write"])
        self.assertFalse(receipt["pointer_promotion"])
        self.assertFalse(receipt["new_global_bind"])
        self.assertTrue(receipt["zero_spend"])

    def test_receipt_roundtrip_and_hash(self):
        fixed = datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc)
        receipt = run_canary.run_bounded_canary(now=fixed)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "receipt.json"
            digest, sidecar_name = run_canary.write_receipt(path, receipt)
            self.assertEqual(digest, run_canary.sha256_bytes(path.read_bytes()))
            self.assertEqual(sidecar_name, "receipt.json.sha256")
            run_canary.verify_receipt(path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["control_plane_source_sha256"], run_canary.FROZEN_SOURCE_SHA256)

    def test_wrong_source_hash_fails_closed_before_import(self):
        old = run_canary.FROZEN_SOURCE_SHA256
        try:
            run_canary.FROZEN_SOURCE_SHA256 = "0" * 64
            with self.assertRaisesRegex(RuntimeError, "HOLD_CONTROL_PLANE_SOURCE_IDENTITY_MISMATCH"):
                run_canary.load_engine()
        finally:
            run_canary.FROZEN_SOURCE_SHA256 = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
