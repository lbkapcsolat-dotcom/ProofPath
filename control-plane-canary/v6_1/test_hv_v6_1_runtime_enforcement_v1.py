#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import alpha_full_6d_local_control_plane_v6_1 as core

FIXED_NOW = datetime(2026, 9, 11, 1, 30, tzinfo=timezone.utc)
VALID_WORKLOAD = b'{"action":"audit","target_system":"isolated_sandbox","payload":{"x":1}}'


def load_adapter():
    path = Path(os.environ.get("HV_ENFORCEMENT_MODULE_PATH", BASE / "hv_v6_1_runtime_enforcement_v1.py"))
    if not path.exists():
        raise AssertionError("RUNTIME_ENFORCEMENT_MODULE_REQUIRED")
    spec = importlib.util.spec_from_file_location("hv_runtime_under_test", path)
    if spec is None or spec.loader is None:
        raise AssertionError("RUNTIME_ENFORCEMENT_MODULE_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_context(*, nonce: str, ttl_seconds: int = 300):
    keys = core.generate_role_keys()
    raw_export_sha256 = core.sha256_bytes(("state:" + nonce).encode("utf-8"))
    return core.build_valid_context(
        role_keys=keys,
        workload_bytes=VALID_WORKLOAD,
        raw_export_sha256=raw_export_sha256,
        nonce=nonce,
        now=FIXED_NOW,
        ttl_seconds=ttl_seconds,
    )


def make_request(adapter, *, candidate_id: str, authority_context, evidence_state="PROVEN_SUFFICIENT", claim_level=None, requires_recovery=False, support_only=False):
    return adapter.RuntimeRequest(
        candidate_id=candidate_id,
        evidence_state=evidence_state,
        authority_context=authority_context,
        claim_level=claim_level if claim_level is not None else adapter.ClaimLevel.LOCAL_TEST,
        requires_recovery=requires_recovery,
        support_only=support_only,
    )


def resolve(adapter, request, ledger, *, now=FIXED_NOW, edge=None, state=None, policy=None):
    context = request.authority_context
    if context is not None:
        edge = context["input_sha256"] if edge is None else edge
        state = context["raw_export_sha256"] if state is None else state
        policy = context["policy_sha256"] if policy is None else policy
    else:
        edge = edge or core.sha256_bytes(b"candidate-edge")
        state = state or core.sha256_bytes(b"candidate-state")
        policy = policy or core.policy_sha256()
    return adapter.resolve_hv_runtime(
        request,
        ledger,
        now=now,
        current_edge_sha256=edge,
        current_state_sha256=state,
        current_policy_sha256=policy,
    )


class HVRuntimeEnforcementConformanceV1(unittest.TestCase):
    def test_obl_01_missing_v_no_execution(self):
        a = load_adapter(); ledger = a.HVRuntimeLedger(claim_ceiling=a.ClaimLevel.LOCAL_TEST)
        req = make_request(a, candidate_id="obl01", authority_context=None, evidence_state="UNKNOWN")
        self.assertFalse(resolve(a, req, ledger).executable)

    def test_obl_02_invalid_v_no_execution(self):
        a = load_adapter(); ctx = valid_context(nonce="obl02")
        ctx = copy.deepcopy(ctx); ctx["provider_statement"]["signature_b64"] = "AAAA"
        req = make_request(a, candidate_id="obl02", authority_context=ctx)
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)).executable)

    def test_obl_03_edge_mutation_invalidates_witness(self):
        a = load_adapter(); ctx = valid_context(nonce="obl03")
        req = make_request(a, candidate_id="obl03", authority_context=ctx)
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST), edge="0" * 64).executable)

    def test_obl_04_state_mutation_invalidates_witness(self):
        a = load_adapter(); ctx = valid_context(nonce="obl04")
        req = make_request(a, candidate_id="obl04", authority_context=ctx)
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST), state="1" * 64).executable)

    def test_obl_05_policy_mutation_requires_revalidation(self):
        a = load_adapter(); ctx = valid_context(nonce="obl05")
        req = make_request(a, candidate_id="obl05", authority_context=ctx)
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST), policy="2" * 64).executable)

    def test_obl_06_reused_nonce_is_rejected(self):
        a = load_adapter(); ctx = valid_context(nonce="obl06")
        ledger = a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST); req = make_request(a, candidate_id="obl06", authority_context=ctx)
        self.assertTrue(resolve(a, req, ledger).executable)
        self.assertFalse(resolve(a, req, ledger).executable)

    def test_obl_07_expired_witness_is_rejected(self):
        a = load_adapter(); ctx = valid_context(nonce="obl07", ttl_seconds=1)
        req = make_request(a, candidate_id="obl07", authority_context=ctx)
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST), now=FIXED_NOW + timedelta(seconds=2)).executable)

    def test_obl_08_newer_revocation_dominates_authority(self):
        a = load_adapter(); ctx = valid_context(nonce="obl08")
        ledger = a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST); ledger.revoke(ctx)
        req = make_request(a, candidate_id="obl08", authority_context=ctx)
        self.assertFalse(resolve(a, req, ledger).executable)

    def test_obl_09_claim_above_ceiling_is_blocked(self):
        a = load_adapter(); ctx = valid_context(nonce="obl09")
        ledger = a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)
        req = make_request(a, candidate_id="obl09", authority_context=ctx, claim_level=a.ClaimLevel.GLOBAL)
        self.assertFalse(resolve(a, req, ledger).executable)

    def test_obl_10_unknown_evidence_maps_to_hold(self):
        a = load_adapter(); ctx = valid_context(nonce="obl10")
        req = make_request(a, candidate_id="obl10", authority_context=ctx, evidence_state="UNKNOWN")
        d = resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST))
        self.assertFalse(d.executable); self.assertEqual(d.k_state, "HOLD")

    def test_obl_11_candidate_persists_without_v(self):
        a = load_adapter(); ledger = a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)
        req = make_request(a, candidate_id="obl11", authority_context=None, evidence_state="UNKNOWN")
        resolve(a, req, ledger)
        self.assertIn("obl11", ledger.candidates)

    def test_obl_12_runtime_cannot_derive_recovery_authority(self):
        a = load_adapter(); ctx = valid_context(nonce="obl12")
        req = make_request(a, candidate_id="obl12", authority_context=ctx, requires_recovery=True)
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)).executable)

    def test_obl_13_k_hold_plus_valid_v_is_non_executable(self):
        a = load_adapter(); ctx = valid_context(nonce="obl13")
        req = make_request(a, candidate_id="obl13", authority_context=ctx, evidence_state="UNKNOWN")
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)).executable)

    def test_obl_14_k_deny_plus_valid_v_is_non_executable(self):
        a = load_adapter(); ctx = valid_context(nonce="obl14")
        req = make_request(a, candidate_id="obl14", authority_context=ctx, evidence_state="PROVEN_NEGATIVE")
        self.assertFalse(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)).executable)

    def test_obl_15_k_pass_plus_absent_v_is_non_executable(self):
        a = load_adapter(); ledger = a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)
        req = make_request(a, candidate_id="obl15", authority_context=None, evidence_state="PROVEN_SUFFICIENT")
        self.assertFalse(resolve(a, req, ledger).executable)

    def test_obl_16_exact_fresh_valid_v_is_executable_subject_to_all_guards(self):
        a = load_adapter(); ctx = valid_context(nonce="obl16")
        req = make_request(a, candidate_id="obl16", authority_context=ctx)
        self.assertTrue(resolve(a, req, a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)).executable)

    def test_obl_17_h_only_authority_mint_is_rejected(self):
        a = load_adapter()
        with self.assertRaises(PermissionError):
            a.attempt_horizontal_mint_v({"candidate": "obl17"})

    def test_obl_18_support_path_is_non_actuating(self):
        a = load_adapter(); ctx = valid_context(nonce="obl18")
        ledger = a.HVRuntimeLedger(a.ClaimLevel.LOCAL_TEST)
        req = make_request(a, candidate_id="obl18", authority_context=ctx, support_only=True)
        self.assertFalse(resolve(a, req, ledger).executable)
        self.assertFalse(any(a.support_mutations().values()))
        self.assertEqual(ledger.consumed_nonces, set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
