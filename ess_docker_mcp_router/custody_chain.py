import hashlib
import json
import re
from pathlib import Path


class CustodyChainError(RuntimeError):
    pass


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha_file(path):
    return _sha_bytes(Path(path).read_bytes())


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha_json(value):
    return _sha_bytes(_canonical_bytes(value))


def _read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception as exc:
        raise CustodyChainError(f"JSON_READ_FAILED:{Path(path).as_posix()}") from exc


def _require_sha(name, value):
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise CustodyChainError(f"INVALID_SHA256:{name}")


def _verify_manifest(root):
    root = Path(root)
    manifest = root / "sha256-manifest.txt"
    if not manifest.is_file():
        raise CustodyChainError("MANIFEST_MISSING")
    entries = {}
    errors = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        try:
            digest, size, rel = line.split("  ", 2)
        except ValueError as exc:
            raise CustodyChainError("MANIFEST_PARSE_ERROR") from exc
        if rel in entries:
            raise CustodyChainError(f"MANIFEST_DUPLICATE:{rel}")
        _require_sha(f"manifest:{rel}", digest)
        p = root / rel
        if not p.is_file():
            errors.append(f"missing:{rel}")
        else:
            b = p.read_bytes()
            if len(b) != int(size):
                errors.append(f"bytes:{rel}")
            if _sha_bytes(b) != digest:
                errors.append(f"sha:{rel}")
        entries[rel] = {"sha256": digest, "bytes": int(size)}
    if errors:
        raise CustodyChainError("MANIFEST_CONTENT_MISMATCH:" + ",".join(errors[:8]))
    return entries


def _index_by_surface(rows, label):
    if not isinstance(rows, list):
        raise CustodyChainError(f"{label}_NOT_LIST")
    out = {}
    for row in rows:
        surface = row.get("surface") if isinstance(row, dict) else None
        if not isinstance(surface, str) or not surface:
            raise CustodyChainError(f"{label}_SURFACE_INVALID")
        if surface in out:
            raise CustodyChainError(f"{label}_DUPLICATE_SURFACE:{surface}")
        out[surface] = row
    return out


def _receipt_files_by_surface(paths, label):
    out = {}
    for p in paths:
        row = _read_json(p)
        surface = row.get("surface") if isinstance(row, dict) else None
        if not isinstance(surface, str) or not surface:
            raise CustodyChainError(f"{label}_SURFACE_INVALID:{Path(p).as_posix()}")
        if surface in out:
            raise CustodyChainError(f"{label}_DUPLICATE_SURFACE:{surface}")
        out[surface] = {"receipt": row, "path": Path(p)}
    return out


def _verify_final_leaf(final_artifact, key, path):
    expected = final_artifact.get(key)
    _require_sha(key, expected)
    actual = _sha_file(path)
    if expected != actual:
        raise CustodyChainError(f"FINAL_RECEIPT_LEAF_MISMATCH:{key}")
    return actual


def verify_provider_custody(
    *,
    artifact_zip,
    extracted_root,
    expected_artifact_sha256,
    expected_artifact_id,
    final_receipt,
    expected_surface_count,
    verify_zip_bytes=True,
):
    artifact_zip = Path(artifact_zip)
    root = Path(extracted_root)
    _require_sha("expected_artifact_sha256", expected_artifact_sha256)
    if verify_zip_bytes:
        if not artifact_zip.is_file():
            raise CustodyChainError("PROVIDER_ARTIFACT_MISSING")
        if _sha_file(artifact_zip) != expected_artifact_sha256:
            raise CustodyChainError("PROVIDER_ARTIFACT_SHA256_MISMATCH")

    final_artifact = final_receipt.get("final_provider_artifact") if isinstance(final_receipt, dict) else None
    if not isinstance(final_artifact, dict):
        raise CustodyChainError("FINAL_RECEIPT_PROVIDER_ARTIFACT_MISSING")
    if final_artifact.get("artifact_id") != expected_artifact_id:
        raise CustodyChainError("FINAL_RECEIPT_ARTIFACT_ID_MISMATCH")
    if final_artifact.get("provider_artifact_sha256") != expected_artifact_sha256:
        raise CustodyChainError("FINAL_RECEIPT_PROVIDER_SHA256_MISMATCH")

    manifest_entries = _verify_manifest(root)
    required_files = {
        "summary.json",
        "bounded-receipt.json",
        "primary-receipt-index.json",
        "replay-results.json",
        "comparisons/replay-comparisons.json",
        "negative/receipt-negative-canaries.json",
        "authority-continuity.json",
    }
    missing_manifest = sorted(required_files - set(manifest_entries))
    if missing_manifest:
        raise CustodyChainError("MANIFEST_REQUIRED_LEAF_MISSING:" + ",".join(missing_manifest))

    summary_sha = _verify_final_leaf(final_artifact, "summary_sha256", root / "summary.json")
    bounded_sha = _verify_final_leaf(final_artifact, "bounded_receipt_sha256", root / "bounded-receipt.json")
    manifest_sha = _verify_final_leaf(final_artifact, "manifest_sha256", root / "sha256-manifest.txt")
    comparisons_sha = _verify_final_leaf(final_artifact, "replay_comparisons_sha256", root / "comparisons" / "replay-comparisons.json")
    negative_sha = _verify_final_leaf(final_artifact, "negative_canaries_sha256", root / "negative" / "receipt-negative-canaries.json")
    authority_sha = _verify_final_leaf(final_artifact, "authority_continuity_sha256", root / "authority-continuity.json")

    summary = _read_json(root / "summary.json")
    bounded = _read_json(root / "bounded-receipt.json")
    if summary != bounded:
        raise CustodyChainError("SUMMARY_BOUNDED_RECEIPT_MISMATCH")

    primary_rows = _index_by_surface(_read_json(root / "primary-receipt-index.json"), "PRIMARY_INDEX")
    replay_rows = _index_by_surface(_read_json(root / "replay-results.json"), "REPLAY_INDEX")
    comparison_rows = _index_by_surface(_read_json(root / "comparisons" / "replay-comparisons.json"), "COMPARISON_INDEX")
    primary_files = _receipt_files_by_surface(sorted((root / "primary-receipts").glob("*.json")), "PRIMARY_RECEIPT_SET")
    replay_files = _receipt_files_by_surface(sorted((root / "replay").glob("*/receipt.json")), "REPLAY_RECEIPT_SET")

    expected_surfaces = set(primary_rows)
    if len(expected_surfaces) != expected_surface_count:
        raise CustodyChainError("SURFACE_COUNT_MISMATCH")
    if set(replay_rows) != expected_surfaces or set(comparison_rows) != expected_surfaces:
        raise CustodyChainError("CHAIN_SURFACE_SET_MISMATCH")
    if set(primary_files) != expected_surfaces:
        raise CustodyChainError("PRIMARY_RECEIPT_SET_MISMATCH")
    if set(replay_files) != expected_surfaces:
        raise CustodyChainError("REPLAY_RECEIPT_SET_MISMATCH")

    for surface in sorted(expected_surfaces):
        p_idx = primary_rows[surface]
        r_idx = replay_rows[surface]
        p_rec = primary_files[surface]["receipt"]
        r_rec = replay_files[surface]["receipt"]
        cmp_row = comparison_rows[surface]
        actual_replay_rel = replay_files[surface]["path"].relative_to(root).as_posix()
        expected_replay_rel = cmp_row.get("replay_receipt_path")
        if expected_replay_rel != actual_replay_rel:
            raise CustodyChainError(f"REPLAY_RECEIPT_PATH_MISMATCH:{surface}")
        if p_idx.get("receipt_sha256") != p_rec.get("receipt_sha256") or p_idx.get("response_sha256") != p_rec.get("response_sha256"):
            raise CustodyChainError(f"PRIMARY_RECEIPT_SET_MISMATCH:{surface}")
        if r_idx.get("receipt_sha256") != r_rec.get("receipt_sha256") or r_idx.get("response_sha256") != r_rec.get("response_sha256"):
            raise CustodyChainError(f"REPLAY_RECEIPT_SET_MISMATCH:{surface}")
        if p_idx.get("transport") != p_rec.get("transport") or r_idx.get("transport") != r_rec.get("transport"):
            raise CustodyChainError(f"RECEIPT_TRANSPORT_MISMATCH:{surface}")
        if cmp_row.get("primary_receipt_sha256") != p_rec.get("receipt_sha256"):
            raise CustodyChainError(f"COMPARISON_CHAIN_MISMATCH:{surface}:primary")
        if cmp_row.get("replay_receipt_sha256") != r_rec.get("receipt_sha256"):
            raise CustodyChainError(f"COMPARISON_CHAIN_MISMATCH:{surface}:replay")
        if cmp_row.get("replay_valid") is not True:
            raise CustodyChainError(f"COMPARISON_CHAIN_INVALID:{surface}")

    if summary.get("primary_receipt_count") != expected_surface_count:
        raise CustodyChainError("SUMMARY_PRIMARY_COUNT_MISMATCH")
    if summary.get("independent_replay_receipt_count") != expected_surface_count:
        raise CustodyChainError("SUMMARY_REPLAY_COUNT_MISMATCH")

    chain = {
        "provider_artifact_sha256": expected_artifact_sha256,
        "provider_artifact_id": expected_artifact_id,
        "manifest_sha256": manifest_sha,
        "manifest_entry_count": len(manifest_entries),
        "summary_sha256": summary_sha,
        "bounded_receipt_sha256": bounded_sha,
        "primary_receipt_index_sha256": _sha_file(root / "primary-receipt-index.json"),
        "replay_results_sha256": _sha_file(root / "replay-results.json"),
        "replay_comparisons_sha256": comparisons_sha,
        "negative_canaries_sha256": negative_sha,
        "authority_continuity_sha256": authority_sha,
        "surface_count": expected_surface_count,
        "surfaces": sorted(expected_surfaces),
    }
    chain_sha = _sha_json(chain)
    return {
        "custody_valid": True,
        "primary_receipt_count": len(primary_rows),
        "replay_receipt_count": len(replay_rows),
        "comparison_count": len(comparison_rows),
        "manifest_entry_count": len(manifest_entries),
        "chain": chain,
        "chain_sha256": chain_sha,
    }
