import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from custody_chain import CustodyChainError, verify_provider_custody


GATE = "ESS_DOCKER_MCP_PROVIDER_ARTIFACT_TAMPER_CROSS_RUN_RECEIPT_SWAP_AND_CHAIN_BREAK_CANARIES_V1"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rebuild_manifest(root):
    root = Path(root)
    lines = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name == "sha256-manifest.txt":
            continue
        rel = p.relative_to(root).as_posix()
        b = p.read_bytes()
        lines.append(f"{sha_bytes(b)}  {len(b)}  {rel}")
    (root / "sha256-manifest.txt").write_text("\n".join(lines) + "\n")


def verify_expect_error(name, work_root, artifact_zip, artifact_sha, artifact_id, receipt, marker, expected_surface_count=12, verify_zip_bytes=False):
    try:
        verify_provider_custody(
            artifact_zip=artifact_zip,
            extracted_root=work_root,
            expected_artifact_sha256=artifact_sha,
            expected_artifact_id=artifact_id,
            final_receipt=receipt,
            expected_surface_count=expected_surface_count,
            verify_zip_bytes=verify_zip_bytes,
        )
    except CustodyChainError as exc:
        observed = str(exc)
        if marker not in observed:
            raise AssertionError(f"{name}: expected marker {marker!r}, observed {observed!r}") from exc
        return {"canary": name, "status": "DENY_PASS", "expected_marker": marker, "observed_error": observed}
    raise AssertionError(f"{name}: tamper unexpectedly passed custody verification")


def copy_source(source_root, temp_parent, name):
    dst = Path(temp_parent) / name
    shutil.copytree(source_root, dst)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-zip", required=True)
    ap.add_argument("--artifact-root", required=True)
    ap.add_argument("--final-receipt", required=True)
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-sha256", required=True)
    ap.add_argument("--source-run-id", required=True, type=int)
    ap.add_argument("--source-head-sha", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    artifact_zip = Path(args.artifact_zip)
    source_root = Path(args.artifact_root)
    final_receipt = json.loads(Path(args.final_receipt).read_text())
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    clean = verify_provider_custody(
        artifact_zip=artifact_zip,
        extracted_root=source_root,
        expected_artifact_sha256=args.artifact_sha256,
        expected_artifact_id=args.artifact_id,
        final_receipt=final_receipt,
        expected_surface_count=12,
        verify_zip_bytes=True,
    )
    assert clean["manifest_entry_count"] == 313, clean
    assert clean["primary_receipt_count"] == 12
    assert clean["replay_receipt_count"] == 12
    assert clean["comparison_count"] == 12

    source_readback = {
        "gate": GATE,
        "source_run_id": args.source_run_id,
        "source_head_sha": args.source_head_sha,
        "source_artifact_id": args.artifact_id,
        "source_artifact_sha256": args.artifact_sha256,
        "source_artifact_bytes": artifact_zip.stat().st_size,
        "source_internal_manifest_checked": clean["manifest_entry_count"],
        "source_primary_receipt_count": clean["primary_receipt_count"],
        "source_replay_receipt_count": clean["replay_receipt_count"],
        "source_comparison_count": clean["comparison_count"],
        "clean_custody_chain_sha256": clean["chain_sha256"],
        "clean_custody_valid": clean["custody_valid"],
    }
    write_json(out / "source-custody-readback.json", source_readback)

    canaries = []
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)

        # 1. Provider ZIP byte tamper. This must fail before any internal semantic inspection.
        tampered_zip = temp / "provider-byte-tamper.zip"
        tampered_zip.write_bytes(artifact_zip.read_bytes() + b"CUSTODY_TAMPER")
        canaries.append(verify_expect_error(
            "provider_zip_byte_tamper",
            source_root,
            tampered_zip,
            args.artifact_sha256,
            args.artifact_id,
            copy.deepcopy(final_receipt),
            "PROVIDER_ARTIFACT_SHA256_MISMATCH",
            verify_zip_bytes=True,
        ))

        # 2. Internal manifest leaf byte tamper, without rehashing manifest.
        root = copy_source(source_root, temp, "manifest-leaf-byte-tamper")
        p = root / "summary.json"
        p.write_bytes(p.read_bytes() + b" ")
        canaries.append(verify_expect_error(
            "manifest_leaf_byte_tamper",
            root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            copy.deepcopy(final_receipt),
            "MANIFEST_CONTENT_MISMATCH",
        ))

        # Load canonical comparison rows once so receipt paths are authority-bearing edges.
        base_comparisons = json.loads((source_root / "comparisons" / "replay-comparisons.json").read_text())
        assert len(base_comparisons) == 12
        first, second = base_comparisons[0], base_comparisons[1]

        # 3. Replay receipt swap after attacker rehashes the internal manifest.
        root = copy_source(source_root, temp, "replay-receipt-swap")
        a = root / first["replay_receipt_path"]
        b = root / second["replay_receipt_path"]
        ab, bb = a.read_bytes(), b.read_bytes()
        a.write_bytes(bb); b.write_bytes(ab)
        rebuild_manifest(root)
        receipt = copy.deepcopy(final_receipt)
        receipt["final_provider_artifact"]["manifest_sha256"] = sha_file(root / "sha256-manifest.txt")
        canaries.append(verify_expect_error(
            "cross_run_replay_receipt_swap_rehashed_manifest",
            root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            receipt,
            "REPLAY_RECEIPT_PATH_MISMATCH",
        ))

        # 4. Primary receipt swap after attacker rehashes the internal manifest.
        root = copy_source(source_root, temp, "primary-receipt-swap")
        a = root / "primary-receipts" / f"{first['surface']}.json"
        b = root / "primary-receipts" / f"{second['surface']}.json"
        ab, bb = a.read_bytes(), b.read_bytes()
        a.write_bytes(bb); b.write_bytes(ab)
        rebuild_manifest(root)
        receipt = copy.deepcopy(final_receipt)
        receipt["final_provider_artifact"]["manifest_sha256"] = sha_file(root / "sha256-manifest.txt")
        canaries.append(verify_expect_error(
            "primary_receipt_swap_rehashed_manifest",
            root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            receipt,
            "PRIMARY_RECEIPT_PATH_MISMATCH",
        ))

        # 5. Comparison edge rebind attempt. Rehash both manifest and comparison leaf in copied final receipt.
        root = copy_source(source_root, temp, "comparison-edge-break")
        cp = root / "comparisons" / "replay-comparisons.json"
        rows = json.loads(cp.read_text())
        rows[0]["replay_receipt_sha256"] = rows[1]["replay_receipt_sha256"]
        write_json(cp, rows)
        rebuild_manifest(root)
        receipt = copy.deepcopy(final_receipt)
        fa = receipt["final_provider_artifact"]
        fa["manifest_sha256"] = sha_file(root / "sha256-manifest.txt")
        fa["replay_comparisons_sha256"] = sha_file(cp)
        canaries.append(verify_expect_error(
            "comparison_edge_break_rehashed",
            root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            receipt,
            "COMPARISON_CHAIN_MISMATCH",
        ))

        # 6. Final receipt leaf lineage break, artifact untouched.
        receipt = copy.deepcopy(final_receipt)
        receipt["final_provider_artifact"]["summary_sha256"] = "0" * 64
        canaries.append(verify_expect_error(
            "final_receipt_leaf_lineage_break",
            source_root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            receipt,
            "FINAL_RECEIPT_LEAF_MISMATCH:summary_sha256",
            verify_zip_bytes=True,
        ))

        # 7. Final receipt provider digest lineage break, artifact untouched.
        receipt = copy.deepcopy(final_receipt)
        receipt["final_provider_artifact"]["provider_artifact_sha256"] = "0" * 64
        canaries.append(verify_expect_error(
            "final_provider_sha_lineage_break",
            source_root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            receipt,
            "FINAL_RECEIPT_PROVIDER_SHA256_MISMATCH",
            verify_zip_bytes=True,
        ))

        # 8. Remove one replay result and rehash the manifest. Must fail on semantic surface-set continuity.
        root = copy_source(source_root, temp, "surface-set-chain-break")
        rp = root / "replay-results.json"
        rows = json.loads(rp.read_text())
        assert len(rows) == 12
        write_json(rp, rows[:-1])
        rebuild_manifest(root)
        receipt = copy.deepcopy(final_receipt)
        receipt["final_provider_artifact"]["manifest_sha256"] = sha_file(root / "sha256-manifest.txt")
        canaries.append(verify_expect_error(
            "surface_set_chain_break_rehashed_manifest",
            root,
            artifact_zip,
            args.artifact_sha256,
            args.artifact_id,
            receipt,
            "CHAIN_SURFACE_SET_MISMATCH",
        ))

    assert len(canaries) == 8
    assert all(row["status"] == "DENY_PASS" for row in canaries)
    write_json(out / "tamper-canaries.json", canaries)

    implementation = {
        "custody_chain_py_sha256": sha_file(Path(__file__).with_name("custody_chain.py")),
        "provider_custody_gate_runner_py_sha256": sha_file(Path(__file__)),
        "test_provider_custody_chain_py_sha256": sha_file(Path(__file__).with_name("test_provider_custody_chain.py")),
    }
    write_json(out / "implementation-sha256.json", implementation)

    summary = {
        "gate": GATE,
        "verdict": "PASS_CLEAN_PROVIDER_CUSTODY_CHAIN__8_OF_8_TAMPER_SWAP_AND_CHAIN_BREAK_CANARIES_FAIL_CLOSED",
        "source_run_id": args.source_run_id,
        "source_head_sha": args.source_head_sha,
        "source_artifact_id": args.artifact_id,
        "source_artifact_sha256": args.artifact_sha256,
        "source_internal_manifest_checked": clean["manifest_entry_count"],
        "source_primary_receipt_count": clean["primary_receipt_count"],
        "source_replay_receipt_count": clean["replay_receipt_count"],
        "source_comparison_count": clean["comparison_count"],
        "clean_custody_chain_sha256": clean["chain_sha256"],
        "tamper_canary_count": len(canaries),
        "tamper_canary_status_counts": {"DENY_PASS": sum(r["status"] == "DENY_PASS" for r in canaries)},
        "new_mcp_live_calls": 0,
        "zero_spend": True,
        "secret_injected": False,
        "external_actuation": False,
        "production_ready": False,
        "runtime_admission": False,
        "global_bind": False,
        "claim_boundary": "FROZEN_PROVIDER_ARTIFACT_CUSTODY_TAMPER_AND_SWAP_CANARIES_ONLY__NO_NEW_MCP_LIVE_CALLS__NO_PRODUCTION_READY__NO_RUNTIME_ADMISSION__NO_GLOBAL_BIND",
    }
    write_json(out / "summary.json", summary)

    manifest_lines = []
    for p in sorted(out.rglob("*")):
        if not p.is_file() or p.name == "sha256-manifest.txt":
            continue
        b = p.read_bytes()
        manifest_lines.append(f"{sha_bytes(b)}  {len(b)}  {p.relative_to(out).as_posix()}")
    (out / "sha256-manifest.txt").write_text("\n".join(manifest_lines) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
