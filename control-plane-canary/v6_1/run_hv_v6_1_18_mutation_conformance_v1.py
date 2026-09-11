#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ADAPTER = BASE / "hv_v6_1_runtime_enforcement_v1.py"
TEST = BASE / "test_hv_v6_1_runtime_enforcement_v1.py"
SCHEMA = "HV_REFERENCE_CHECKER_TO_V6_1_RUNTIME_ENFORCEMENT_MUTATION_RECEIPT_V1"
PASS_VERDICT = "PASS_HV_V6_1_RUNTIME_ENFORCEMENT_MUTATION_CONFORMANCE_18_OF_18"

MUTATIONS = {
    "OBL-01": (
        'return _hold("OBL-01", "HOLD_MISSING_V", "MISSING_VERTICAL_AUTHORITY")',
        'return _pass("OBL-01", "MUTANT_DEFAULT_ALLOW_WITHOUT_V")',
        "test_obl_01_missing_v_no_execution",
    ),
    "OBL-02": (
        'return _hold("OBL-02", "HOLD_INVALID_V", core_decision.verdict)',
        'return _pass("OBL-02", "MUTANT_INVALID_V_ALLOWED")',
        "test_obl_02_invalid_v_no_execution",
    ),
    "OBL-03": (
        'return _hold("OBL-03", "HOLD_EDGE_BIND_MISMATCH", "EDGE_CHANGED_AFTER_APPROVAL")',
        'return _pass("OBL-03", "MUTANT_EDGE_SUBSTITUTION_ALLOWED")',
        "test_obl_03_edge_mutation_invalidates_witness",
    ),
    "OBL-04": (
        'return _hold("OBL-04", "HOLD_STATE_BIND_MISMATCH", "STATE_CHANGED_AFTER_APPROVAL")',
        'return _pass("OBL-04", "MUTANT_STALE_STATE_ALLOWED")',
        "test_obl_04_state_mutation_invalidates_witness",
    ),
    "OBL-05": (
        'return _hold("OBL-05", "HOLD_POLICY_BIND_MISMATCH", "POLICY_CHANGED_AFTER_APPROVAL")',
        'return _pass("OBL-05", "MUTANT_STALE_POLICY_ALLOWED")',
        "test_obl_05_policy_mutation_requires_revalidation",
    ),
    "OBL-06": (
        'return _hold("OBL-06", "HOLD_REPLAYED_V", "NONCE_ALREADY_CONSUMED")',
        'return _pass("OBL-06", "MUTANT_REPLAY_ALLOWED")',
        "test_obl_06_reused_nonce_is_rejected",
    ),
    "OBL-07": (
        'return _hold("OBL-07", "HOLD_EXPIRED_V", "AUTHORITY_NOT_FRESH")',
        'return _pass("OBL-07", "MUTANT_EXPIRED_AUTHORITY_ALLOWED")',
        "test_obl_07_expired_witness_is_rejected",
    ),
    "OBL-08": (
        'return _hold("OBL-08", "HOLD_REVOKED_V", "NEWER_REVOCATION_DOMINATES")',
        'return _pass("OBL-08", "MUTANT_REVOKED_AUTHORITY_ALLOWED")',
        "test_obl_08_newer_revocation_dominates_authority",
    ),
    "OBL-09": (
        'return _hold("OBL-09", "HOLD_CLAIM_ABOVE_CEILING", "CLAIM_ESCALATION_BLOCKED")',
        'return _pass("OBL-09", "MUTANT_CLAIM_ESCALATION_ALLOWED")',
        "test_obl_09_claim_above_ceiling_is_blocked",
    ),
    "OBL-10": (
        '"UNKNOWN": "HOLD",',
        '"UNKNOWN": "PASS",  # MUTANT_UNKNOWN_DEFAULT_ALLOW',
        "test_obl_10_unknown_evidence_maps_to_hold",
    ),
    "OBL-11": (
        'ledger.record_candidate(request.candidate_id)',
        'pass  # MUTANT_CANDIDATE_PERSISTENCE_REMOVED',
        "test_obl_11_candidate_persists_without_v",
    ),
    "OBL-12": (
        'return _hold("OBL-12", "HOLD_RECOVERY_AUTHORITY_EXTERNAL_REQUIRED", "RUNTIME_CANNOT_DERIVE_RECOVERY_AUTHORITY")',
        'return _pass("OBL-12", "MUTANT_RUNTIME_SELF_RECOVERY_ALLOWED")',
        "test_obl_12_runtime_cannot_derive_recovery_authority",
    ),
    "OBL-13": (
        'return _hold("OBL-13", "HOLD_K_STATE", "K_HOLD_NONEXECUTABLE", k_state=k_state)',
        'return _pass("OBL-13", "MUTANT_K_HOLD_ALLOWED", k_state=k_state)',
        "test_obl_13_k_hold_plus_valid_v_is_non_executable",
    ),
    "OBL-14": (
        'return _hold("OBL-14", "DENY_K_STATE", "K_DENY_NONEXECUTABLE", k_state=k_state)',
        'return _pass("OBL-14", "MUTANT_K_DENY_ALLOWED", k_state=k_state)',
        "test_obl_14_k_deny_plus_valid_v_is_non_executable",
    ),
    "OBL-15": (
        'return _hold("OBL-15", "HOLD_PASS_WITHOUT_V", "K_PASS_REQUIRES_VERTICAL_AUTHORITY", k_state=k_state)',
        'return _pass("OBL-15", "MUTANT_K_PASS_WITHOUT_V_ALLOWED", k_state=k_state)',
        "test_obl_15_k_pass_plus_absent_v_is_non_executable",
    ),
    "OBL-16": (
        'return _pass("OBL-16", "ALL_RUNTIME_GUARDS_SATISFIED", k_state=k_state)',
        'return _hold("OBL-16", "HOLD_MUTANT_FALSE_NEGATIVE", "VALID_AUTHORITY_BLOCKED", k_state=k_state)',
        "test_obl_16_exact_fresh_valid_v_is_executable_subject_to_all_guards",
    ),
    "OBL-17": (
        'raise PermissionError("H_ONLY_CANNOT_MINT_V")',
        'return True  # MUTANT_H_ONLY_MINT_ALLOWED',
        "test_obl_17_h_only_authority_mint_is_rejected",
    ),
    "OBL-18": (
        '"pointer": False,  # OBL-18',
        '"pointer": True,  # MUTANT_SUPPORT_POINTER_WRITE',
        "test_obl_18_support_path_is_non_actuating",
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(cmd, *, env=None):
    proc = subprocess.run(cmd, cwd=BASE, env=env, capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stdout, proc.stderr


def load_adapter(path: Path):
    spec = importlib.util.spec_from_file_location("hv_runtime_mapping_for_receipt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("HOLD_ADAPTER_IMPORT_SPEC")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if not ADAPTER.exists():
        print(json.dumps({"schema": SCHEMA, "verdict": "HOLD_RUNTIME_ENFORCEMENT_MODULE_MISSING"}, sort_keys=True))
        return 1

    base_env = os.environ.copy()
    base_env.pop("HV_ENFORCEMENT_MODULE_PATH", None)
    baseline_rc, baseline_out, baseline_err = run([sys.executable, str(TEST)], env=base_env)
    if baseline_rc != 0:
        print(json.dumps({
            "schema": SCHEMA,
            "verdict": "HOLD_BASELINE_18_CASE_CONFORMANCE_FAILED",
            "baseline_returncode": baseline_rc,
            "baseline_tail": (baseline_out + baseline_err)[-3000:],
        }, sort_keys=True))
        return 1

    source = ADAPTER.read_text(encoding="utf-8")
    adapter = load_adapter(ADAPTER)
    expected_obls = {f"OBL-{i:02d}" for i in range(1, 19)}
    if set(adapter.OBLIGATION_TO_HOOK) != expected_obls:
        print(json.dumps({"schema": SCHEMA, "verdict": "HOLD_MAPPING_NOT_18_OF_18"}, sort_keys=True))
        return 1

    cases = []
    with tempfile.TemporaryDirectory(prefix="hv_mutants_", dir=BASE) as td:
        td_path = Path(td)
        for obl in sorted(MUTATIONS):
            old, new, test_name = MUTATIONS[obl]
            count = source.count(old)
            if count != 1:
                cases.append({"obligation": obl, "status": "HOLD_MUTATION_TARGET_COUNT", "target_count": count})
                continue
            mutated = source.replace(old, new, 1)
            mutant_path = td_path / f"mutant_{obl.replace('-', '_')}.py"
            mutant_path.write_text(mutated, encoding="utf-8")

            compile_rc, compile_out, compile_err = run([sys.executable, "-m", "py_compile", str(mutant_path)], env=base_env)
            if compile_rc != 0:
                cases.append({
                    "obligation": obl,
                    "status": "HOLD_MUTANT_COMPILE_ERROR",
                    "compile_tail": (compile_out + compile_err)[-1200:],
                })
                continue

            env = base_env.copy()
            env["HV_ENFORCEMENT_MODULE_PATH"] = str(mutant_path)
            test_id = f"HVRuntimeEnforcementConformanceV1.{test_name}"
            rc, out, err = run([sys.executable, str(TEST), test_id], env=env)
            combined = out + err
            assertion_kill = rc != 0 and "FAILED (failures=1)" in combined and "errors=" not in combined
            cases.append({
                "obligation": obl,
                "test": test_id,
                "mutant_sha256": sha256_bytes(mutated.encode("utf-8")),
                "compile_pass": True,
                "test_returncode": rc,
                "assertion_kill": assertion_kill,
                "status": "PASS_MUTANT_KILLED" if assertion_kill else "HOLD_MUTANT_SURVIVED_OR_ERRORED",
            })

    killed = sum(c["status"] == "PASS_MUTANT_KILLED" for c in cases)
    verdict = PASS_VERDICT if len(cases) == 18 and killed == 18 else "HOLD_HV_V6_1_RUNTIME_ENFORCEMENT_MUTATION_CONFORMANCE"
    receipt = {
        "schema": SCHEMA,
        "adapter_source_sha256": sha256_bytes(ADAPTER.read_bytes()),
        "core_source_sha256": sha256_bytes((BASE / "alpha_full_6d_local_control_plane_v6_1.py").read_bytes()),
        "baseline_tests": "PASS_18_OF_18" if baseline_rc == 0 else "HOLD",
        "mapping": adapter.OBLIGATION_TO_HOOK,
        "mutations_total": 18,
        "mutations_killed": killed,
        "cases": cases,
        "claims": {
            "bounded_v6_1_runtime_enforcement_adapter_conformance": verdict == PASS_VERDICT,
            "original_core_alone_enforces_all_18": False,
            "runtime_admission": False,
            "production_readiness": False,
            "global_bind": False,
            "pointer_promotion": False,
        },
        "zero_spend": True,
        "verdict": verdict,
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if verdict == PASS_VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
