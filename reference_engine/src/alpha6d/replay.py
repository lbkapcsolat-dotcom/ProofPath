"""Isolated deterministic suite replay and byte/SHA closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from alpha6d.canary_runner import run_suite
from alpha6d.canonical import canonical_json_bytes


_ARTIFACTS = ("outputs.json", "receipts.json")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matches_expected(fixture: dict, result: dict) -> bool:
    return all(result["output"].get(key) == expected for key, expected in fixture["expected"].items())


def write_suite_run(fixtures_path: str | Path, output_dir: str | Path) -> dict:
    fixtures_path = Path(fixtures_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = run_suite(fixtures)

    outputs = [
        {"name": result["name"], "module": result["module"], "output": result["output"]}
        for result in results
    ]
    receipts = [
        {
            "name": result["name"],
            "receipt": result["receipt"],
            "receipt_sha256": result["receipt_sha256"],
        }
        for result in results
    ]

    (output_dir / "outputs.json").write_bytes(canonical_json_bytes(outputs) + b"\n")
    (output_dir / "receipts.json").write_bytes(canonical_json_bytes(receipts) + b"\n")

    manifest_lines = [f"{_file_sha256(output_dir / name)}  {name}" for name in sorted(_ARTIFACTS)]
    (output_dir / "manifest.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    expected_match_count = sum(
        1 for fixture, result in zip(fixtures, results) if _matches_expected(fixture, result)
    )
    return {
        "canary_count": len(fixtures),
        "expected_match_count": expected_match_count,
        "outputs_sha256": _file_sha256(output_dir / "outputs.json"),
        "receipts_sha256": _file_sha256(output_dir / "receipts.json"),
        "manifest_sha256": _file_sha256(output_dir / "manifest.sha256"),
    }


def compare_runs(run_a_dir: str | Path, run_b_dir: str | Path) -> dict:
    run_a = Path(run_a_dir)
    run_b = Path(run_b_dir)
    names = (*_ARTIFACTS, "manifest.sha256")
    byte_equal = {name: (run_a / name).read_bytes() == (run_b / name).read_bytes() for name in names}
    sha_equal = {name: _file_sha256(run_a / name) == _file_sha256(run_b / name) for name in names}
    return {
        "byte_exact_equal": all(byte_equal.values()),
        "sha256_equal": all(sha_equal.values()),
        "byte_equal_by_file": byte_equal,
        "sha256_equal_by_file": sha_equal,
    }
