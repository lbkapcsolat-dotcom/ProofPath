import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from custody_chain import CustodyChainError, verify_provider_custody


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rebuild_manifest(root):
    lines = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name == "sha256-manifest.txt":
            continue
        rel = p.relative_to(root).as_posix()
        b = p.read_bytes()
        lines.append(f"{sha_bytes(b)}  {len(b)}  {rel}")
    (root / "sha256-manifest.txt").write_text("\n".join(lines) + "\n")


def make_fixture(base):
    root = base / "artifact"
    (root / "primary-receipts").mkdir(parents=True)
    (root / "replay" / "01-alpha").mkdir(parents=True)
    (root / "replay" / "02-beta").mkdir(parents=True)
    (root / "comparisons").mkdir(parents=True)
    (root / "negative").mkdir(parents=True)

    primary = []
    replay = []
    comparisons = []
    for i, surface in enumerate(("alpha", "beta"), start=1):
        p_receipt = {
            "surface": surface,
            "transport": "gateway-profile",
            "receipt_sha256": f"{i}" * 64,
            "response_sha256": f"{i+2}" * 64,
        }
        r_receipt = {
            "surface": surface,
            "transport": "gateway-profile",
            "receipt_sha256": f"{i+4}" * 64,
            "response_sha256": f"{i+6}" * 64,
        }
        write_json(root / "primary-receipts" / f"{surface}.json", p_receipt)
        replay_rel = f"replay/0{i}-{surface}/receipt.json"
        write_json(root / replay_rel, r_receipt)
        primary.append({
            "surface": surface,
            "transport": "gateway-profile",
            "receipt_sha256": p_receipt["receipt_sha256"],
            "response_sha256": p_receipt["response_sha256"],
        })
        replay.append({
            "surface": surface,
            "transport": "gateway-profile",
            "receipt_sha256": r_receipt["receipt_sha256"],
            "response_sha256": r_receipt["response_sha256"],
            "status": "REPLAY_RECEIPT_BOUND_PASS",
        })
        comparisons.append({
            "surface": surface,
            "transport": "gateway-profile",
            "primary_receipt_sha256": p_receipt["receipt_sha256"],
            "replay_receipt_sha256": r_receipt["receipt_sha256"],
            "replay_receipt_path": replay_rel,
            "replay_valid": True,
        })

    summary = {
        "gate": "TEST_GATE",
        "primary_receipt_count": 2,
        "independent_replay_receipt_count": 2,
        "receipt_negative_canary_count": 1,
        "verdict": "PASS",
    }
    write_json(root / "primary-receipt-index.json", primary)
    write_json(root / "replay-results.json", replay)
    write_json(root / "comparisons" / "replay-comparisons.json", comparisons)
    write_json(root / "negative" / "receipt-negative-canaries.json", [{"canary": "x", "status": "DENY_PASS"}])
    write_json(root / "authority-continuity.json", {"ok": True})
    write_json(root / "summary.json", summary)
    write_json(root / "bounded-receipt.json", summary)
    rebuild_manifest(root)

    zip_path = base / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(root).as_posix())
    artifact_sha = sha_bytes(zip_path.read_bytes())
    final_receipt = {
        "final_provider_artifact": {
            "artifact_id": 123,
            "provider_artifact_sha256": artifact_sha,
            "summary_sha256": sha_bytes((root / "summary.json").read_bytes()),
            "bounded_receipt_sha256": sha_bytes((root / "bounded-receipt.json").read_bytes()),
            "manifest_sha256": sha_bytes((root / "sha256-manifest.txt").read_bytes()),
            "replay_comparisons_sha256": sha_bytes((root / "comparisons" / "replay-comparisons.json").read_bytes()),
            "negative_canaries_sha256": sha_bytes((root / "negative" / "receipt-negative-canaries.json").read_bytes()),
            "authority_continuity_sha256": sha_bytes((root / "authority-continuity.json").read_bytes()),
        }
    }
    return root, zip_path, artifact_sha, final_receipt


class ProviderCustodyChainTests(unittest.TestCase):
    def test_clean_provider_chain_passes_and_returns_chain_commitment(self):
        with tempfile.TemporaryDirectory() as td:
            root, zip_path, artifact_sha, final_receipt = make_fixture(Path(td))
            result = verify_provider_custody(
                artifact_zip=zip_path,
                extracted_root=root,
                expected_artifact_sha256=artifact_sha,
                expected_artifact_id=123,
                final_receipt=final_receipt,
                expected_surface_count=2,
            )
            self.assertTrue(result["custody_valid"])
            self.assertEqual(2, result["primary_receipt_count"])
            self.assertEqual(2, result["replay_receipt_count"])
            self.assertRegex(result["chain_sha256"], r"^[0-9a-f]{64}$")

    def test_provider_zip_byte_tamper_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root, zip_path, artifact_sha, final_receipt = make_fixture(Path(td))
            zip_path.write_bytes(zip_path.read_bytes() + b"tamper")
            with self.assertRaisesRegex(CustodyChainError, "PROVIDER_ARTIFACT_SHA256_MISMATCH"):
                verify_provider_custody(
                    artifact_zip=zip_path,
                    extracted_root=root,
                    expected_artifact_sha256=artifact_sha,
                    expected_artifact_id=123,
                    final_receipt=final_receipt,
                    expected_surface_count=2,
                )

    def test_cross_run_receipt_swap_fails_even_after_manifest_rehash(self):
        with tempfile.TemporaryDirectory() as td:
            root, zip_path, artifact_sha, final_receipt = make_fixture(Path(td))
            a = root / "replay" / "01-alpha" / "receipt.json"
            b = root / "replay" / "02-beta" / "receipt.json"
            ab, bb = a.read_bytes(), b.read_bytes()
            a.write_bytes(bb)
            b.write_bytes(ab)
            rebuild_manifest(root)
            final_receipt["final_provider_artifact"]["manifest_sha256"] = sha_bytes((root / "sha256-manifest.txt").read_bytes())
            with self.assertRaisesRegex(CustodyChainError, "REPLAY_RECEIPT_PATH_MISMATCH"):
                verify_provider_custody(
                    artifact_zip=zip_path,
                    extracted_root=root,
                    expected_artifact_sha256=artifact_sha,
                    expected_artifact_id=123,
                    final_receipt=final_receipt,
                    expected_surface_count=2,
                    verify_zip_bytes=False,
                )

    def test_comparison_chain_break_fails_even_after_manifest_rehash(self):
        with tempfile.TemporaryDirectory() as td:
            root, zip_path, artifact_sha, final_receipt = make_fixture(Path(td))
            p = root / "comparisons" / "replay-comparisons.json"
            rows = json.loads(p.read_text())
            rows[0]["replay_receipt_sha256"] = rows[1]["replay_receipt_sha256"]
            write_json(p, rows)
            rebuild_manifest(root)
            f = final_receipt["final_provider_artifact"]
            f["manifest_sha256"] = sha_bytes((root / "sha256-manifest.txt").read_bytes())
            f["replay_comparisons_sha256"] = sha_bytes(p.read_bytes())
            with self.assertRaisesRegex(CustodyChainError, "COMPARISON_CHAIN_MISMATCH"):
                verify_provider_custody(
                    artifact_zip=zip_path,
                    extracted_root=root,
                    expected_artifact_sha256=artifact_sha,
                    expected_artifact_id=123,
                    final_receipt=final_receipt,
                    expected_surface_count=2,
                    verify_zip_bytes=False,
                )

    def test_final_receipt_lineage_break_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root, zip_path, artifact_sha, final_receipt = make_fixture(Path(td))
            broken = copy.deepcopy(final_receipt)
            broken["final_provider_artifact"]["summary_sha256"] = "0" * 64
            with self.assertRaisesRegex(CustodyChainError, "FINAL_RECEIPT_LEAF_MISMATCH:summary_sha256"):
                verify_provider_custody(
                    artifact_zip=zip_path,
                    extracted_root=root,
                    expected_artifact_sha256=artifact_sha,
                    expected_artifact_id=123,
                    final_receipt=broken,
                    expected_surface_count=2,
                )


if __name__ == "__main__":
    unittest.main()
