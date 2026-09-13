from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_MATHLIB_REVISION = "0df444a360eaa60ab8c11dca51a86af692955474"
EXPECTED_TOOLCHAIN = b"leanprover/lean4:v4.33.1\n"
ORACLE_SCHEMA = "MATHLIB_RUNTIME_ORACLE_V1"
WITNESS_NAME = "ZMOD4_H1_BOUNDARY_TIMES_2"
ORACLE_KEYS = [
    "schema",
    "witness",
    "degree",
    "representatives",
    "custom_class_equality",
    "mathlib_class_equality",
    "class_equal",
    "negative_control",
]
EXPECTED_MATRIX = [
    [True, False, True, False],
    [False, True, False, True],
    [True, False, True, False],
    [False, True, False, True],
]
EXPECTED_NEGATIVE_MATRIX = [
    [True, False, False, False],
    [False, True, False, False],
    [False, False, True, False],
    [False, False, False, True],
]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"MISSING_{label}")


def _read_mathlib_revision(lake_manifest_path: Path) -> str:
    try:
        manifest = json.loads(lake_manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_LAKE_MANIFEST") from exc

    matches = [
        package
        for package in manifest.get("packages", [])
        if isinstance(package, dict) and package.get("name") == "mathlib"
    ]
    if len(matches) != 1:
        raise ValueError("MATHLIB_MANIFEST_ENTRY_COUNT_MISMATCH")

    mathlib = matches[0]
    revision = mathlib.get("rev")
    input_revision = mathlib.get("inputRev")
    if (
        revision != EXPECTED_MATHLIB_REVISION
        or input_revision != EXPECTED_MATHLIB_REVISION
    ):
        raise ValueError("MATHLIB_REVISION_MISMATCH")
    return revision


def build_engine_identity(
    package_root: Path | str,
    binary_path: Path | str,
    git_head_sha: str,
) -> tuple[dict[str, Any], str]:
    package = Path(package_root)
    binary = Path(binary_path)

    if re.fullmatch(r"[0-9a-f]{40}", git_head_sha) is None:
        raise ValueError("INVALID_GIT_HEAD_SHA")

    oracle_source = package / "RuntimeBindOracle.lean"
    bridge_source = package / "MathlibHomologicalComplexBridge.lean"
    nat_homology_source = package / "NatIndexedHomologyGate.lean"
    toolchain = package / "lean-toolchain"
    lake_manifest = package / "lake-manifest.json"

    for path, label in (
        (oracle_source, "ORACLE_SOURCE"),
        (bridge_source, "BRIDGE_SOURCE"),
        (nat_homology_source, "NAT_HOMOLOGY_SOURCE"),
        (toolchain, "LEAN_TOOLCHAIN"),
        (lake_manifest, "LAKE_MANIFEST"),
        (binary, "ORACLE_BINARY"),
    ):
        _require_file(path, label)

    if toolchain.read_bytes() != EXPECTED_TOOLCHAIN:
        raise ValueError("LEAN_TOOLCHAIN_MISMATCH")

    mathlib_revision = _read_mathlib_revision(lake_manifest)

    engine_manifest = {
        "schema": "MATHLIB_RUNTIME_ENGINE_ID_V1",
        "git_head_sha": git_head_sha,
        "oracle_source_sha256": sha256_file(oracle_source),
        "bridge_source_sha256": sha256_file(bridge_source),
        "nat_homology_source_sha256": sha256_file(nat_homology_source),
        "lean_toolchain_sha256": sha256_file(toolchain),
        "lake_manifest_sha256": sha256_file(lake_manifest),
        "mathlib_revision": mathlib_revision,
        "oracle_binary_sha256": sha256_file(binary),
    }
    engine_sha256 = sha256_bytes(canonical_json_bytes(engine_manifest))
    return engine_manifest, engine_sha256


def validate_oracle_output(raw: bytes, *, negative: bool) -> dict[str, Any]:
    if not isinstance(raw, bytes):
        raise ValueError("ORACLE_OUTPUT_NOT_BYTES")
    if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise ValueError("ORACLE_OUTPUT_NEWLINE_CONTRACT_VIOLATION")

    try:
        text = raw[:-1].decode("utf-8", errors="strict")
        payload = json.loads(text)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("ORACLE_OUTPUT_INVALID_JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("ORACLE_OUTPUT_NOT_OBJECT")
    if list(payload.keys()) != ORACLE_KEYS:
        raise ValueError("ORACLE_KEY_ORDER_MISMATCH")

    if payload.get("schema") != ORACLE_SCHEMA:
        raise ValueError("ORACLE_SCHEMA_MISMATCH")
    if payload.get("witness") != WITNESS_NAME:
        raise ValueError("ORACLE_WITNESS_MISMATCH")
    if payload.get("degree") != 1:
        raise ValueError("ORACLE_DEGREE_MISMATCH")
    if payload.get("representatives") != [0, 1, 2, 3]:
        raise ValueError("ORACLE_REPRESENTATIVES_MISMATCH")
    if payload.get("custom_class_equality") != EXPECTED_MATRIX:
        raise ValueError("CUSTOM_CLASS_MATRIX_MISMATCH")

    if negative:
        if (
            payload.get("negative_control") is not True
            or payload.get("class_equal") is not False
        ):
            raise ValueError("NEGATIVE_CONTROL_NOT_DETECTED")
        if payload.get("mathlib_class_equality") != EXPECTED_NEGATIVE_MATRIX:
            raise ValueError("NEGATIVE_MATHLIB_MATRIX_MISMATCH")
    else:
        if payload.get("negative_control") is not False:
            raise ValueError("POSITIVE_ORACLE_MARKED_NEGATIVE")
        if payload.get("class_equal") is not True:
            raise ValueError("POSITIVE_CLASS_EQUALITY_NOT_ESTABLISHED")
        if payload.get("mathlib_class_equality") != EXPECTED_MATRIX:
            raise ValueError("POSITIVE_MATHLIB_MATRIX_MISMATCH")

    reencoded = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    if reencoded != raw:
        raise ValueError("ORACLE_NONCANONICAL_JSON")
    return payload


def witness_descriptor() -> dict[str, Any]:
    return {
        "schema": "MATHLIB_RUNTIME_WITNESS_V1",
        "witness": WITNESS_NAME,
        "degree": 1,
        "representatives": [0, 1, 2, 3],
        "expected_class_equality": EXPECTED_MATRIX,
        "negative_mathlib_class_equality": EXPECTED_NEGATIVE_MATRIX,
    }


def build_receipt(
    *,
    git_head_sha: str,
    engine_sha256: str,
    oracle_binary_sha256: str,
    witness_sha256: str,
    positive_output_sha256: str,
    negative_output_sha256: str,
    negative_control_detected: bool,
    replay_output_equal: bool,
) -> dict[str, Any]:
    if negative_control_detected is not True:
        raise ValueError("NEGATIVE_CONTROL_NOT_DETECTED")
    if replay_output_equal is not True:
        raise ValueError("POSITIVE_REPLAY_MISMATCH")

    return {
        "schema": "MATHLIB_RUNTIME_BIND_RECEIPT_V1",
        "formal_gate": "PASS_MATHLIB_HOMOLOGICAL_COMPLEX_INTEROPERABILITY_AND_HOMOLOGY_BRIDGE_V1",
        "authority_scope": "ISOLATED_CI_CANARY_ONLY",
        "git_head_sha": git_head_sha,
        "engine_sha256": engine_sha256,
        "oracle_binary_sha256": oracle_binary_sha256,
        "mathlib_revision": EXPECTED_MATHLIB_REVISION,
        "witness_sha256": witness_sha256,
        "positive_output_sha256": positive_output_sha256,
        "negative_output_sha256": negative_output_sha256,
        "custom_vs_mathlib_class_equal": True,
        "negative_control_detected": True,
        "replay_output_equal": True,
        "receipt_replay_equal": True,
        "general_runtime_admission": False,
        "global_bind": False,
        "pointer_promotion": False,
        "production_readiness": False,
        "zero_spend": True,
    }


def _run_process(argv: list[str], *, cwd: Path, label: str) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{label}_EXIT_{completed.returncode}:{detail}")
    return completed


def _git_head(repo_root: Path) -> str:
    completed = _run_process(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, label="GIT_HEAD_READ"
    )
    if completed.stderr != b"":
        raise RuntimeError("GIT_HEAD_UNEXPECTED_STDERR")
    head = completed.stdout.decode("ascii", errors="strict").strip()
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise RuntimeError("GIT_HEAD_INVALID")
    return head


def _resolved_mathlib_revision(package_root: Path) -> str:
    mathlib_checkout = package_root / ".lake" / "packages" / "mathlib"
    if not mathlib_checkout.is_dir():
        raise RuntimeError("MATHLIB_CHECKOUT_MISSING")
    completed = _run_process(
        ["git", "rev-parse", "HEAD"],
        cwd=mathlib_checkout,
        label="MATHLIB_HEAD_READ",
    )
    if completed.stderr != b"":
        raise RuntimeError("MATHLIB_HEAD_UNEXPECTED_STDERR")
    revision = completed.stdout.decode("ascii", errors="strict").strip()
    if revision != EXPECTED_MATHLIB_REVISION:
        raise RuntimeError("MATHLIB_CHECKOUT_REVISION_MISMATCH")
    return revision


def _build_oracle(package_root: Path) -> None:
    lake = shutil.which("lake")
    if lake is None:
        raise RuntimeError("LAKE_NOT_FOUND")
    _run_process(
        [lake, "build", "runtimeBindOracle"],
        cwd=package_root,
        label="ORACLE_BUILD",
    )


def _run_oracle(binary: Path, package_root: Path, *, negative: bool) -> bytes:
    argv = [str(binary.resolve())]
    if negative:
        argv.append("--negative-control")
    completed = _run_process(argv, cwd=package_root, label="ORACLE_EXECUTION")
    if completed.stderr != b"":
        raise RuntimeError("ORACLE_UNEXPECTED_STDERR")
    validate_oracle_output(completed.stdout, negative=negative)
    return completed.stdout


def _assert_engine_stable(
    package_root: Path,
    binary: Path,
    git_head_sha: str,
    expected_manifest: dict[str, Any],
    expected_engine_sha256: str,
) -> None:
    current_manifest, current_engine_sha256 = build_engine_identity(
        package_root, binary, git_head_sha
    )
    if current_manifest != expected_manifest or current_engine_sha256 != expected_engine_sha256:
        raise RuntimeError("ENGINE_IDENTITY_CHANGED_DURING_RUN")


def _write_json(path: Path, value: Any) -> bytes:
    data = canonical_json_bytes(value) + b"\n"
    path.write_bytes(data)
    return data


def _fresh_readback(
    *,
    package_root: Path,
    output_dir: Path,
    binary: Path,
    git_head_sha: str,
    engine_manifest: dict[str, Any],
    engine_sha256: str,
    receipt: dict[str, Any],
) -> bool:
    if _git_head(package_root.parents[1]) != git_head_sha:
        raise RuntimeError("FRESH_GIT_HEAD_MISMATCH")
    _resolved_mathlib_revision(package_root)

    current_manifest, current_engine_sha256 = build_engine_identity(
        package_root, binary, git_head_sha
    )
    if current_manifest != engine_manifest or current_engine_sha256 != engine_sha256:
        raise RuntimeError("FRESH_ENGINE_IDENTITY_MISMATCH")

    engine_bytes = (output_dir / "engine-manifest.json").read_bytes()
    expected_engine_bytes = canonical_json_bytes(engine_manifest) + b"\n"
    if engine_bytes != expected_engine_bytes:
        raise RuntimeError("ENGINE_MANIFEST_READBACK_MISMATCH")

    witness_bytes = (output_dir / "witness.json").read_bytes()
    expected_witness_bytes = canonical_json_bytes(witness_descriptor()) + b"\n"
    if witness_bytes != expected_witness_bytes:
        raise RuntimeError("WITNESS_READBACK_MISMATCH")

    positive_a = (output_dir / "positive-a.json").read_bytes()
    negative = (output_dir / "negative.json").read_bytes()
    positive_b = (output_dir / "positive-b.json").read_bytes()
    validate_oracle_output(positive_a, negative=False)
    validate_oracle_output(negative, negative=True)
    validate_oracle_output(positive_b, negative=False)
    if positive_a != positive_b:
        raise RuntimeError("POSITIVE_REPLAY_READBACK_MISMATCH")

    receipt_a = (output_dir / "receipt-a.json").read_bytes()
    receipt_b = (output_dir / "receipt-b.json").read_bytes()
    receipt_final = (output_dir / "receipt.json").read_bytes()
    expected_receipt_bytes = canonical_json_bytes(receipt) + b"\n"
    if not (
        receipt_a == receipt_b == receipt_final == expected_receipt_bytes
    ):
        raise RuntimeError("RECEIPT_READBACK_MISMATCH")

    if receipt["engine_sha256"] != current_engine_sha256:
        raise RuntimeError("RECEIPT_ENGINE_SHA_MISMATCH")
    if receipt["oracle_binary_sha256"] != sha256_file(binary):
        raise RuntimeError("RECEIPT_BINARY_SHA_MISMATCH")
    if receipt["witness_sha256"] != sha256_bytes(canonical_json_bytes(witness_descriptor())):
        raise RuntimeError("RECEIPT_WITNESS_SHA_MISMATCH")
    if receipt["positive_output_sha256"] != sha256_bytes(positive_a):
        raise RuntimeError("RECEIPT_POSITIVE_SHA_MISMATCH")
    if receipt["negative_output_sha256"] != sha256_bytes(negative):
        raise RuntimeError("RECEIPT_NEGATIVE_SHA_MISMATCH")

    if receipt["authority_scope"] != "ISOLATED_CI_CANARY_ONLY":
        raise RuntimeError("AUTHORITY_SCOPE_MISMATCH")
    for key in (
        "general_runtime_admission",
        "global_bind",
        "pointer_promotion",
        "production_readiness",
    ):
        if receipt[key] is not False:
            raise RuntimeError(f"CLAIM_CEILING_VIOLATION:{key}")
    if receipt["zero_spend"] is not True:
        raise RuntimeError("ZERO_SPEND_VIOLATION")
    return True


def execute_gate(package_root: Path | str, output_dir: Path | str) -> dict[str, Any]:
    package = Path(package_root).resolve()
    output = Path(output_dir)
    repo_root = package.parents[1]

    git_head_sha = _git_head(repo_root)
    _read_mathlib_revision(package / "lake-manifest.json")
    _resolved_mathlib_revision(package)
    _build_oracle(package)

    binary = package / ".lake" / "build" / "bin" / "runtimeBindOracle"
    engine_manifest, engine_sha256 = build_engine_identity(
        package, binary, git_head_sha
    )

    positive_a = _run_oracle(binary, package, negative=False)
    _assert_engine_stable(
        package, binary, git_head_sha, engine_manifest, engine_sha256
    )

    negative = _run_oracle(binary, package, negative=True)
    _assert_engine_stable(
        package, binary, git_head_sha, engine_manifest, engine_sha256
    )

    positive_b = _run_oracle(binary, package, negative=False)
    _assert_engine_stable(
        package, binary, git_head_sha, engine_manifest, engine_sha256
    )

    replay_output_equal = positive_a == positive_b
    if not replay_output_equal:
        raise RuntimeError("POSITIVE_REPLAY_MISMATCH")

    negative_payload = validate_oracle_output(negative, negative=True)
    negative_control_detected = (
        negative_payload["class_equal"] is False
        and negative_payload["negative_control"] is True
    )
    if not negative_control_detected:
        raise RuntimeError("NEGATIVE_CONTROL_NOT_DETECTED")

    witness = witness_descriptor()
    witness_sha256 = sha256_bytes(canonical_json_bytes(witness))
    positive_output_sha256 = sha256_bytes(positive_a)
    negative_output_sha256 = sha256_bytes(negative)

    receipt_a = build_receipt(
        git_head_sha=git_head_sha,
        engine_sha256=engine_sha256,
        oracle_binary_sha256=engine_manifest["oracle_binary_sha256"],
        witness_sha256=witness_sha256,
        positive_output_sha256=positive_output_sha256,
        negative_output_sha256=negative_output_sha256,
        negative_control_detected=negative_control_detected,
        replay_output_equal=replay_output_equal,
    )
    receipt_b = build_receipt(
        git_head_sha=git_head_sha,
        engine_sha256=engine_sha256,
        oracle_binary_sha256=engine_manifest["oracle_binary_sha256"],
        witness_sha256=witness_sha256,
        positive_output_sha256=positive_output_sha256,
        negative_output_sha256=negative_output_sha256,
        negative_control_detected=negative_control_detected,
        replay_output_equal=replay_output_equal,
    )

    receipt_a_bytes = canonical_json_bytes(receipt_a) + b"\n"
    receipt_b_bytes = canonical_json_bytes(receipt_b) + b"\n"
    if receipt_a_bytes != receipt_b_bytes:
        raise RuntimeError("RECEIPT_REPLAY_MISMATCH")

    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "engine-manifest.json", engine_manifest)
    _write_json(output / "witness.json", witness)
    (output / "positive-a.json").write_bytes(positive_a)
    (output / "negative.json").write_bytes(negative)
    (output / "positive-b.json").write_bytes(positive_b)
    (output / "receipt-a.json").write_bytes(receipt_a_bytes)
    (output / "receipt-b.json").write_bytes(receipt_b_bytes)
    (output / "receipt.json").write_bytes(receipt_a_bytes)

    fresh_readback = _fresh_readback(
        package_root=package,
        output_dir=output,
        binary=binary,
        git_head_sha=git_head_sha,
        engine_manifest=engine_manifest,
        engine_sha256=engine_sha256,
        receipt=receipt_a,
    )

    receipt_sha256 = sha256_bytes(receipt_a_bytes)
    return {
        "schema": "MATHLIB_RUNTIME_BIND_CANARY_SUMMARY_V1",
        "status": "PASS_ISOLATED_CI_CANARY_ONLY",
        "git_head_sha": git_head_sha,
        "engine_sha256": engine_sha256,
        "oracle_binary_sha256": engine_manifest["oracle_binary_sha256"],
        "positive_output_sha256": positive_output_sha256,
        "negative_output_sha256": negative_output_sha256,
        "receipt_sha256": receipt_sha256,
        "replay_output_equal": True,
        "receipt_replay_equal": True,
        "negative_control_detected": True,
        "fresh_readback": fresh_readback,
        "general_runtime_admission": False,
        "global_bind": False,
        "pointer_promotion": False,
        "production_readiness": False,
        "zero_spend": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    package_root = Path(__file__).resolve().parents[1]
    summary = execute_gate(package_root, Path(args.output_dir))
    sys.stdout.buffer.write(canonical_json_bytes(summary) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
