import hashlib
import json
import re
from pathlib import Path

SPEC_DRIVE_ID = "1BTwkIu9tQYRYfiWRIkKc44Gi3423RdispjOPAnQb4KE"
SPEC_REVISION_ID = "ANLCKQnIQaax6jGT6rGo8WSjR54jSknxF_FkRJSPpqFHYebuGMTLr9fWh27VtYAUEPE7Wr70Tu5PtjW8xsd6ifvqjhgVL82upQDRVL_FQgU"
SPEC_TITLE = "EQUILIBRIUM_INTEGRATED_AXIOMS_CORE_RECOVERY_CUSTODY_CURRENTNESS_AUTHORITY_FORMAL_SPEC_AND_COUNTERMODEL_V1"
CANONICAL_MAIN_COMMIT = "015a8f418912efd44de0b4edf1650b9374a6e899"
RCCA_SOURCE_SHA256 = "c31496672026e2aa1ef1139dfe30652919bdaabb8ba66c3715b903a3d4b294bf"
IMMUTABLE_PROOF_RELEASE_TAG = "ess-rcca-canonical-main-proof-v1"
IMMUTABLE_PROOF_RELEASE_ID = 386843824
IMMUTABLE_PROOF_MANIFEST_SHA256 = "79318e830db2f85176df618db4e580119a94a946adfc54563ca3649436a27428"
IMMUTABLE_PROOF_BUNDLE_SHA256 = "db0d134b9b4696292c006b0e05521a8465f0a7b0e5c254c1bb6634ccd7d1cdd5"

EXPECTED = {
    "axioms": {
        "RCCA-01": "DIMENSIONAL_SEPARATION",
        "RCCA-02": "EXACT_BYTE_CUSTODY",
        "RCCA-03": "IMMUTABILITY_IS_NOT_AUTHORITY",
        "RCCA-04": "EXACTNESS_IS_NOT_IMMUTABILITY",
        "RCCA-05": "CURRENTNESS_REQUIRES_AUTHENTICATED_LINEAGE_RESOLUTION",
        "RCCA-06": "SUPERSESSION_CHANGES_CURRENTNESS_NOT_HISTORY",
        "RCCA-07": "RECOVERABILITY_IS_NOT_RESTORE_AUTHORITY",
        "RCCA-08": "HISTORICAL_ROLLBACK_REQUIRES_EXPLICIT_RECOVERY_AUTHORITY",
        "RCCA-09": "RUNTIME_AUTHORITY_CANNOT_SUBSTITUTE_FOR_RECOVERY_AUTHORITY",
        "RCCA-10": "EXACT_RECOVERY_WITNESS_BINDING_AND_NONREPLAY",
        "RCCA-11": "ENFORCEMENT_EVIDENCE_SEPARATION",
        "RCCA-12": "NONCOMPENSATORY_RECOVERY_CLAIM_CEILING",
    },
    "countermodels": {
        "CM-RCCA-01": "EXACT_BUT_MUTABLE",
        "CM-RCCA-02": "IMMUTABLE_WRONG_BYTES",
        "CM-RCCA-03": "EXACT_IMMUTABLE_BUT_SUPERSEDED",
        "CM-RCCA-04": "CURRENT_BUT_UNREADABLE",
        "CM-RCCA-05": "RECOVERABLE_WITHOUT_RECOVERY_WITNESS",
        "CM-RCCA-06": "RUNTIME_TOKEN_AS_RECOVERY_TOKEN",
        "CM-RCCA-07": "RECOVERY_WITNESS_BOUND_TO_DIFFERENT_BUNDLE",
        "CM-RCCA-08": "STALE_POLICY_OR_EPOCH",
        "CM-RCCA-09": "CONFIGURED_BUT_NOT_ENFORCED_IMMUTABILITY",
        "CM-RCCA-10": "AUTHORIZED_HISTORICAL_ROLLBACK",
        "CM-RCCA-11": "STRONG_CUSTODY_WITHOUT_ACTION_AUTHORITY",
        "CM-RCCA-12": "SUPERSESSION_WITH_AUDIT_PERSISTENCE",
    },
    "derived_theorems": {
        "T-RCCA-01": "NO_CUSTODY_TO_AUTHORITY_ESCALATION",
        "T-RCCA-02": "SUPERSESSION_DEMOTES_CURRENTNESS_ONLY",
        "T-RCCA-03": "HISTORICAL_ROLLBACK_REQUIRES_EXPLICIT_W_R",
        "T-RCCA-04": "NONCOMPENSATORY_RECOVERY_CEILING",
        "T-RCCA-05": "REPLICA_MULTIPLICITY_DOES_NOT_CREATE_AUTHORITY",
        "T-RCCA-06": "RECOVERY_EXECUTION_IS_EXACT_CONTEXT_BOUND",
        "T-RCCA-07": "ENFORCEMENT_CLAIM_REQUIRES_ENFORCEMENT_EVIDENCE",
        "T-RCCA-08": "REFINEMENT_NONWEAKENING",
    },
}

CM_PRIMARY = {
    "CM-RCCA-01": "cm_exact_but_mutable",
    "CM-RCCA-02": "cm_immutable_wrong_bytes",
    "CM-RCCA-03": "cm_exact_immutable_but_superseded",
    "CM-RCCA-04": "cm_current_but_unreadable",
    "CM-RCCA-05": "cm_recoverable_without_recovery_witness",
    "CM-RCCA-06": "cm_runtime_token_not_recovery_token",
    "CM-RCCA-07": "cm_recovery_witness_wrong_bundle",
    "CM-RCCA-08": "cm_stale_policy_or_epoch",
    "CM-RCCA-09": "cm_configured_not_enforced",
    "CM-RCCA-10": "cm_authorized_historical_rollback",
    "CM-RCCA-11": "cm_strong_custody_without_authority",
    "CM-RCCA-12": "cm_supersession_with_audit_persistence",
}

SYMBOL_RE = re.compile(r"(?m)^\s*(?:private\s+)?(theorem|def|structure|inductive)\s+([A-Za-z0-9_']+)")
THEOREM_RE = re.compile(r"(?m)^\s*(?:private\s+)?theorem\s+([A-Za-z0-9_']+)")
PROOF_ESCAPE_RE = re.compile(r"(?m)^\s*(?:private\s+)?(?:axiom|unsafe)\b|\bsorry\b|\badmit\b")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_coverage(root: Path) -> dict:
    root = Path(root)
    lean_path = root / "formal/rcca-lean4/RCCA.lean"
    manifest_path = root / "formal/rcca-lean4/coverage/rcca-spec-to-lean-coverage.json"
    lean = lean_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    spec = manifest["spec"]
    proof = manifest["proof_custody"]
    spec_revision_bound = (
        spec["drive_id"] == SPEC_DRIVE_ID
        and spec["revision_id"] == SPEC_REVISION_ID
        and spec["title"] == SPEC_TITLE
    )
    source_sha_bound = (
        manifest["lean"]["path"] == "formal/rcca-lean4/RCCA.lean"
        and manifest["lean"]["sha256"] == RCCA_SOURCE_SHA256
        and _sha256(lean_path) == RCCA_SOURCE_SHA256
        and proof["canonical_main_commit"] == CANONICAL_MAIN_COMMIT
        and proof["release_tag"] == IMMUTABLE_PROOF_RELEASE_TAG
        and proof["release_id"] == IMMUTABLE_PROOF_RELEASE_ID
        and proof["manifest_sha256"] == IMMUTABLE_PROOF_MANIFEST_SHA256
        and proof["bundle_sha256"] == IMMUTABLE_PROOF_BUNDLE_SHA256
    )
    if not spec_revision_bound:
        raise AssertionError("pinned Drive formal-spec revision mismatch")
    if not source_sha_bound:
        raise AssertionError("canonical Lean source / immutable proof custody binding mismatch")

    obligations = manifest["obligations"]
    all_ids = []
    referenced_symbols = set()
    for category, expected in EXPECTED.items():
        entries = obligations[category]
        got = {entry["id"]: entry["title"] for entry in entries}
        if got != expected:
            raise AssertionError(f"{category} obligation inventory mismatch: {got!r}")
        for entry in entries:
            if not entry.get("symbols"):
                raise AssertionError(f"{entry['id']} has no mechanized symbol mapping")
            all_ids.append(entry["id"])
            referenced_symbols.update(entry["symbols"])

    if len(all_ids) != len(set(all_ids)):
        raise AssertionError("duplicate primary obligation id")
    if len(all_ids) != 32:
        raise AssertionError(f"expected 32 primary obligations, got {len(all_ids)}")

    declared_symbols = {name for _, name in SYMBOL_RE.findall(lean)}
    lean_theorems = set(THEOREM_RE.findall(lean))
    unknown_manifest_symbols = sorted(referenced_symbols - declared_symbols)
    orphan_lean_theorems = sorted(lean_theorems - referenced_symbols)
    proof_escape_declarations = sorted(set(PROOF_ESCAPE_RE.findall(lean)))

    cm_entries = obligations["countermodels"]
    cm_primary = {entry["id"]: entry.get("primary_theorem") for entry in cm_entries}
    countermodel_direct_bijection = (
        cm_primary == CM_PRIMARY
        and len(set(cm_primary.values())) == 12
        and all(entry["primary_theorem"] in entry["symbols"] for entry in cm_entries)
        and set(cm_primary.values()).issubset(lean_theorems)
    )

    if unknown_manifest_symbols:
        raise AssertionError(f"unknown manifest symbols: {unknown_manifest_symbols}")
    if orphan_lean_theorems:
        raise AssertionError(f"orphan Lean theorems: {orphan_lean_theorems}")
    if proof_escape_declarations:
        raise AssertionError(f"proof escape declarations: {proof_escape_declarations}")
    if not countermodel_direct_bijection:
        raise AssertionError("countermodel id-to-primary-theorem bijection failed")

    return {
        "spec_revision_bound": spec_revision_bound,
        "source_sha_bound": source_sha_bound,
        "axiom_coverage": "12/12",
        "countermodel_coverage": "12/12",
        "derived_theorem_coverage": "8/8",
        "primary_obligation_bijection": "32/32",
        "countermodel_direct_bijection": countermodel_direct_bijection,
        "declared_lean_theorem_count": len(lean_theorems),
        "referenced_symbol_count": len(referenced_symbols),
        "unknown_manifest_symbols": unknown_manifest_symbols,
        "orphan_lean_theorems": orphan_lean_theorems,
        "proof_escape_declarations": proof_escape_declarations,
        "canonical_main_commit": CANONICAL_MAIN_COMMIT,
        "rcca_source_sha256": RCCA_SOURCE_SHA256,
        "spec_drive_id": SPEC_DRIVE_ID,
        "spec_revision_id": SPEC_REVISION_ID,
        "immutable_proof_release_tag": IMMUTABLE_PROOF_RELEASE_TAG,
        "claim_ceiling": "PINNED_SPEC_TO_CANONICAL_LEAN_COVERAGE_BIJECTION_AND_NO_ORPHAN_PROOF_ONLY",
        "core_admission": False,
        "runtime_admission": False,
        "production_promotion": False,
        "pointer_promotion": False,
        "global_bind": False,
        "zero_spend": True,
        "verdict": "PASS_RCCA_SPEC_TO_LEAN_COVERAGE_BIJECTION_AND_NO_ORPHAN_PROOF",
    }
