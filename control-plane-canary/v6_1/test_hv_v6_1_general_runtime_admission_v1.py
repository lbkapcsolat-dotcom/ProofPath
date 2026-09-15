#!/usr/bin/env python3
from __future__ import annotations

import unittest

import hv_v6_1_runtime_enforcement_v1 as adapter

REQUIRED_OBLIGATIONS = [f"OBL-{i:02d}" for i in range(1, 19)]
REQUIRED_NEGATIVE_CONTROLS = {
    "h_to_v_mint_rejected": True,
    "pass_without_v_rejected": True,
    "unknown_evidence_hold": True,
    "invalid_v_rejected": True,
    "replay_rejected": True,
    "revocation_dominates": True,
}


def good_evidence():
    return {
        "persistence_rehydration_guard": "PASS_HV_V6_1_INERT_ARTIFACT_FRESH_PROCESS_H_TO_V_REJECTION_3_OF_3",
        "obligations_passed": list(REQUIRED_OBLIGATIONS),
        "negative_controls": dict(REQUIRED_NEGATIVE_CONTROLS),
    }


class GeneralRuntimeAdmissionV1(unittest.TestCase):
    def test_01_admission_api_exists(self):
        self.assertTrue(callable(getattr(adapter, "admit_general_runtime_v1", None)))

    def test_02_exact_complete_evidence_admits_runtime(self):
        fn = getattr(adapter, "admit_general_runtime_v1", None)
        self.assertTrue(callable(fn))
        out = fn(good_evidence())
        self.assertTrue(out["general_runtime_admission"])
        self.assertEqual(out["scope"], "HV_V6_1_CONTROL_PLANE_RUNTIME")
        self.assertEqual(out["verdict"], "PASS_GENERAL_RUNTIME_ADMISSION_V1")
        self.assertFalse(out["production_readiness"])
        self.assertFalse(out["global_bind"])
        self.assertFalse(out["pointer_promotion"])
        self.assertFalse(out["main_merge"])

    def test_03_missing_persistence_guard_fails_closed(self):
        fn = getattr(adapter, "admit_general_runtime_v1", None)
        self.assertTrue(callable(fn))
        evidence = good_evidence()
        evidence["persistence_rehydration_guard"] = "HOLD"
        out = fn(evidence)
        self.assertFalse(out["general_runtime_admission"])
        self.assertEqual(out["verdict"], "HOLD_PERSISTENCE_REHYDRATION_GUARD")

    def test_04_missing_obligation_fails_closed(self):
        fn = getattr(adapter, "admit_general_runtime_v1", None)
        self.assertTrue(callable(fn))
        evidence = good_evidence()
        evidence["obligations_passed"].remove("OBL-17")
        out = fn(evidence)
        self.assertFalse(out["general_runtime_admission"])
        self.assertEqual(out["verdict"], "HOLD_OBLIGATION_COVERAGE")
        self.assertIn("OBL-17", out["missing_obligations"])

    def test_05_negative_control_failure_fails_closed(self):
        fn = getattr(adapter, "admit_general_runtime_v1", None)
        self.assertTrue(callable(fn))
        evidence = good_evidence()
        evidence["negative_controls"]["replay_rejected"] = False
        out = fn(evidence)
        self.assertFalse(out["general_runtime_admission"])
        self.assertEqual(out["verdict"], "HOLD_NEGATIVE_CONTROL")
        self.assertIn("replay_rejected", out["failed_negative_controls"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
