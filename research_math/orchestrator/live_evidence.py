from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ENGINE_FAMILIES = {
    "lean": "lean_kernel",
    "arb": "flint_arb",
    "julia": "julia_runtime",
    "sage": "cas_sage",
}

PROFILES: dict[str, dict[str, Any]] = {
    "lean": {
        "engine": "lean",
        "version_regex": r"Lean \(version (?P<version>4\.33\.1),",
        "inputs": [
            "research_math/lean/ResearchMathP0.lean",
            "research_math/lean/lakefile.lean",
            "research_math/lean/lean-toolchain",
        ],
        "evidence": [
            {
                "claim_id": "THM-LIVE",
                "role": "formal_kernel_proof",
                "marker": "PROOFPATH_EVIDENCE THM-LIVE formal_kernel_proof formal_target=ResearchMathP0.square_nonnegative",
                "extra": {"formal_target": "ResearchMathP0.square_nonnegative"},
            }
        ],
        "adversarial": [],
    },
    "arb": {
        "engine": "arb",
        "version_regex": r"python-flint version: (?P<version>0\.9\.0)",
        "inputs": [
            "research_math/flint/canary.py",
            "research_math/flint/requirements.txt",
        ],
        "evidence": [
            {
                "claim_id": "RIG-LIVE",
                "role": "rigorous_enclosure",
                "marker": "PROOFPATH_EVIDENCE RIG-LIVE rigorous_enclosure residual_contains_zero=true",
                "extra": {},
            }
        ],
        "adversarial": [
            {
                "claim_id": "RIG-LIVE",
                "category": "boundary",
                "marker": "PROOFPATH_ADVERSARIAL RIG-LIVE boundary roundtrip_contains_one=true",
            }
        ],
    },
    "julia": {
        "engine": "julia",
        "version_regex": r"Julia version: (?P<version>1\.12\.7)",
        "inputs": ["research_math/julia/canary.jl"],
        "evidence": [
            {
                "claim_id": "ALG-LIVE",
                "role": "independent_exact_crosscheck",
                "marker": "PROOFPATH_EVIDENCE ALG-LIVE independent_exact_crosscheck factor_product=4294967295",
                "extra": {},
            },
            {
                "claim_id": "HPC-LIVE",
                "role": "hpc_computation",
                "marker": "PROOFPATH_EVIDENCE HPC-LIVE hpc_computation threaded_sum=500000500000",
                "extra": {},
            },
        ],
        "adversarial": [],
    },
    "sage": {
        "engine": "sage",
        "version_regex": r"SageMath version: (?P<version>10\.9)",
        "inputs": ["research_math/sage/canary.py"],
        "evidence": [
            {
                "claim_id": "ALG-LIVE",
                "role": "exact_computation",
                "marker": "PROOFPATH_EVIDENCE ALG-LIVE exact_computation factor_product=4294967295",
                "extra": {},
            },
            {
                "claim_id": "THM-LIVE",
                "role": "independent_countercheck",
                "marker": "PROOFPATH_EVIDENCE THM-LIVE independent_countercheck rational_scan=true",
                "extra": {},
            },
            {
                "claim_id": "RIG-LIVE",
                "role": "independent_crosscheck",
                "marker": "PROOFPATH_EVIDENCE RIG-LIVE independent_crosscheck sqrt2_residual_lt_1e-70=true",
                "extra": {},
            },
            {
                "claim_id": "HPC-LIVE",
                "role": "deterministic_independent_replay",
                "marker": "PROOFPATH_EVIDENCE HPC-LIVE deterministic_independent_replay serial_sum=500000500000",
                "extra": {},
            },
        ],
        "adversarial": [
            {
                "claim_id": "ALG-LIVE",
                "category": "boundary",
                "marker": "PROOFPATH_ADVERSARIAL ALG-LIVE boundary factor_product_exact=true",
            },
            {
                "claim_id": "THM-LIVE",
                "category": "boundary",
                "marker": "PROOFPATH_ADVERSARIAL THM-LIVE boundary zero_and_sign_cases=true",
            },
            {
                "claim_id": "THM-LIVE",
                "category": "counterexample_search",
                "marker": "PROOFPATH_ADVERSARIAL THM-LIVE counterexample_search rational_scan_no_counterexample=true",
            },
            {
                "claim_id": "HPC-LIVE",
                "category": "boundary",
                "marker": "PROOFPATH_ADVERSARIAL HPC-LIVE boundary serial_formula_small_n=true",
            },
        ],
    },
}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_obj(obj: Any) -> str:
    return _sha_bytes(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _with_hash(body: dict[str, Any], field: str) -> dict[str, Any]:
    out = deepcopy(body)
    out[field] = _sha_obj(body)
    return out


def _verify_hashed_record(record: dict[str, Any], field: str) -> bool:
    digest = record.get(field)
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False
    body = deepcopy(record)
    body.pop(field, None)
    return _sha_obj(body) == digest


def _semantic_record(record: dict[str, Any], *, adversarial: bool) -> dict[str, Any]:
    keys = ["claim_id", "status", "witness_marker"]
    keys.append("category" if adversarial else "role")
    if not adversarial and "formal_target" in record:
        keys.append("formal_target")
    return {key: deepcopy(record.get(key)) for key in keys}


def _engine_identity(receipt: dict[str, Any]) -> dict[str, Any]:
    evidence = sorted(
        (_semantic_record(item, adversarial=False) for item in receipt.get("evidence", [])),
        key=lambda item: (str(item.get("claim_id")), str(item.get("role"))),
    )
    adversarial = sorted(
        (_semantic_record(item, adversarial=True) for item in receipt.get("adversarial", [])),
        key=lambda item: (str(item.get("claim_id")), str(item.get("category"))),
    )
    return {
        "engine_family": receipt["engine_family"],
        "engine_version": receipt["engine_version"],
        "input_sha256": deepcopy(receipt["input_sha256"]),
        "evidence_semantic_sha256": _sha_obj(evidence),
        "adversarial_semantic_sha256": _sha_obj(adversarial),
    }


def emit_receipt(
    profile_name: str,
    *,
    source_sha: str,
    run_id: str,
    job: str,
    raw_log: Path,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    profile = PROFILES.get(profile_name)
    if profile is None:
        raise ValueError(f"unsupported profile: {profile_name}")
    raw = raw_log.read_text(encoding="utf-8")
    version_match = re.search(profile["version_regex"], raw)
    if not version_match:
        raise ValueError(f"{profile_name}: expected engine version not found")

    input_hashes: dict[str, str] = {}
    for rel in profile["inputs"]:
        path = repo_root / rel
        if not path.is_file():
            raise ValueError(f"{profile_name}: missing input file: {rel}")
        input_hashes[rel] = _sha_file(path)

    common = {
        "source_sha": source_sha,
        "run_id": str(run_id),
        "job": job,
        "engine": profile["engine"],
        "engine_family": ENGINE_FAMILIES[profile["engine"]],
        "engine_version": version_match.group("version"),
        "raw_output_sha256": _sha_file(raw_log),
        "input_sha256": input_hashes,
    }

    evidence = []
    for spec in profile["evidence"]:
        if spec["marker"] not in raw:
            raise ValueError(f"{profile_name}: missing evidence marker: {spec['marker']}")
        body = {
            "schema": "proofpath.live_engine_evidence.v1",
            "claim_id": spec["claim_id"],
            "role": spec["role"],
            "status": "PASS",
            **common,
            "witness_marker": spec["marker"],
            **spec.get("extra", {}),
        }
        evidence.append(_with_hash(body, "evidence_sha256"))

    adversarial = []
    for spec in profile["adversarial"]:
        if spec["marker"] not in raw:
            raise ValueError(f"{profile_name}: missing adversarial marker: {spec['marker']}")
        body = {
            "schema": "proofpath.live_adversarial_evidence.v1",
            "claim_id": spec["claim_id"],
            "category": spec["category"],
            "status": "PASS",
            **common,
            "witness_marker": spec["marker"],
        }
        adversarial.append(_with_hash(body, "evidence_sha256"))

    receipt_body = {
        "schema": "proofpath.engine_run_receipt.v1",
        **common,
        "profile": profile_name,
        "status": "PASS",
        "evidence": evidence,
        "adversarial": adversarial,
        "claim_ceiling": "Fresh engine execution evidence only; mathematical PASS remains downstream.",
    }
    receipt = _with_hash(receipt_body, "receipt_sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def verify_receipt(
    receipt_path: Path,
    repo_root: Path,
    expected_source_sha: str | None = None,
) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "proofpath.engine_run_receipt.v1":
        raise ValueError(f"{receipt_path}: bad receipt schema")
    if not _verify_hashed_record(receipt, "receipt_sha256"):
        raise ValueError(f"{receipt_path}: receipt hash mismatch")

    engine = str(receipt.get("engine", ""))
    profile = PROFILES.get(str(receipt.get("profile", "")))
    if profile is None or profile["engine"] != engine:
        raise ValueError(f"{receipt_path}: engine/profile mismatch")
    if receipt.get("engine_family") != ENGINE_FAMILIES.get(engine):
        raise ValueError(f"{receipt_path}: engine family mismatch")
    if expected_source_sha is not None and receipt.get("source_sha") != expected_source_sha:
        raise ValueError(f"{receipt_path}: source SHA mismatch")

    raw_log = receipt_path.with_name("raw.log")
    if not raw_log.is_file() or _sha_file(raw_log) != receipt.get("raw_output_sha256"):
        raise ValueError(f"{receipt_path}: raw output hash mismatch")

    bound_inputs = receipt.get("input_sha256", {})
    if set(bound_inputs) != set(profile["inputs"]):
        raise ValueError(f"{receipt_path}: input set mismatch")
    for rel, expected_hash in bound_inputs.items():
        path = repo_root / rel
        if not path.is_file() or _sha_file(path) != expected_hash:
            raise ValueError(f"{receipt_path}: input hash mismatch for {rel}")

    raw = raw_log.read_text(encoding="utf-8")
    for record in [*receipt.get("evidence", []), *receipt.get("adversarial", [])]:
        if not _verify_hashed_record(record, "evidence_sha256"):
            raise ValueError(f"{receipt_path}: evidence hash mismatch")
        if record.get("engine") != engine or record.get("source_sha") != receipt.get("source_sha"):
            raise ValueError(f"{receipt_path}: evidence lineage mismatch")
        if record.get("run_id") != receipt.get("run_id"):
            raise ValueError(f"{receipt_path}: evidence run mismatch")
        marker = record.get("witness_marker")
        if not isinstance(marker, str) or marker not in raw:
            raise ValueError(f"{receipt_path}: witness readback mismatch")
    return receipt


def bind_receipts(
    *,
    receipts_root: Path,
    repo_root: Path,
    claims_path: Path,
    expected_source_sha: str,
    output_path: Path,
) -> dict[str, Any]:
    receipt_paths = sorted(receipts_root.rglob("receipt.json"))
    if not receipt_paths:
        raise ValueError("no engine receipts found")
    receipts = [verify_receipt(path, repo_root, expected_source_sha) for path in receipt_paths]
    by_engine = {str(receipt["engine"]): receipt for receipt in receipts}
    expected_engines = set(PROFILES)
    if len(receipts) != len(expected_engines) or set(by_engine) != expected_engines:
        raise ValueError(f"engine receipt set mismatch: got={sorted(by_engine)} expected={sorted(expected_engines)}")

    run_ids = {str(receipt["run_id"]) for receipt in receipts}
    if len(run_ids) != 1:
        raise ValueError(f"receipts do not share one run_id: {sorted(run_ids)}")
    if {str(receipt["source_sha"]) for receipt in receipts} != {expected_source_sha}:
        raise ValueError("receipts do not share the expected source SHA")

    claims_payload = json.loads(claims_path.read_text(encoding="utf-8"))
    evidence = [item for receipt in receipts for item in receipt.get("evidence", [])]
    adversarial = [item for receipt in receipts for item in receipt.get("adversarial", [])]

    sys.path.insert(0, str((repo_root / "research_math/orchestrator").resolve()))
    import assurance_pipeline as ap

    assurance_bundle = ap.build_bundle(
        {
            "claims": claims_payload["claims"],
            "evidence": evidence,
            "adversarial": adversarial,
        }
    )
    statuses = {item["id"]: item["status"] for item in assurance_bundle["gate"]["claims"]}
    expected_claims = {item["id"] for item in claims_payload["claims"]}
    if set(statuses) != expected_claims:
        raise ValueError(f"live gate claim set mismatch: {statuses}")
    holds = {claim_id: status for claim_id, status in statuses.items() if status != "PASS"}
    if holds:
        raise ValueError(f"live assurance HOLD: {holds}")

    body = {
        "schema": "proofpath.live_engine_binding.v2",
        "source_sha": expected_source_sha,
        "run_id": next(iter(run_ids)),
        "engine_receipt_sha256": {
            engine: by_engine[engine]["receipt_sha256"] for engine in sorted(by_engine)
        },
        "engine_identity": {
            engine: _engine_identity(by_engine[engine]) for engine in sorted(by_engine)
        },
        "live_claims_sha256": _sha_file(claims_path),
        "assurance_bundle": assurance_bundle,
        "claim_ceiling": "PASS is limited to the four live claims executed and independently evidenced in this exact source/run binding.",
    }
    bound = _with_hash(body, "binding_sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bound, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bound


def _claim_statuses(binding: dict[str, Any]) -> dict[str, str]:
    try:
        claims = binding["assurance_bundle"]["gate"]["claims"]
    except (KeyError, TypeError) as exc:
        raise ValueError("binding missing claim gate") from exc
    return {str(item.get("id")): str(item.get("status")) for item in claims}


def _load_binding(path: Path, expected_source_sha: str) -> dict[str, Any]:
    binding = json.loads(path.read_text(encoding="utf-8"))
    if binding.get("schema") != "proofpath.live_engine_binding.v2":
        raise ValueError(f"{path}: bad binding schema")
    if not _verify_hashed_record(binding, "binding_sha256"):
        raise ValueError(f"{path}: binding hash mismatch")
    if binding.get("source_sha") != expected_source_sha:
        raise ValueError(f"{path}: source SHA mismatch")
    identities = binding.get("engine_identity")
    if not isinstance(identities, dict) or set(identities) != set(PROFILES):
        raise ValueError(f"{path}: engine identity set mismatch")
    statuses = _claim_statuses(binding)
    if not statuses or any(status != "PASS" for status in statuses.values()):
        raise ValueError(f"{path}: non-PASS claim state")
    return binding


def compare_bindings(
    *,
    first_path: Path,
    second_path: Path,
    expected_source_sha: str,
    output_path: Path,
) -> dict[str, Any]:
    first = _load_binding(first_path, expected_source_sha)
    second = _load_binding(second_path, expected_source_sha)

    first_run = str(first.get("run_id", ""))
    second_run = str(second.get("run_id", ""))
    if not first_run or not second_run or first_run == second_run:
        raise ValueError("replay run IDs must differ")
    if first.get("live_claims_sha256") != second.get("live_claims_sha256"):
        raise ValueError("live claims hash drift")
    if first.get("engine_identity") != second.get("engine_identity"):
        raise ValueError("engine identity drift")

    first_statuses = _claim_statuses(first)
    second_statuses = _claim_statuses(second)
    if first_statuses != second_statuses:
        raise ValueError("claim status drift")

    body = {
        "schema": "proofpath.cross_run_receipt_chain.v1",
        "status": "PASS",
        "source_sha": expected_source_sha,
        "run_ids": [first_run, second_run],
        "binding_sha256": [first["binding_sha256"], second["binding_sha256"]],
        "live_claims_sha256": first["live_claims_sha256"],
        "engine_identity_sha256": _sha_obj(first["engine_identity"]),
        "claim_statuses": first_statuses,
        "claim_ceiling": "P12 proves cross-run consistency only for the same four live claims, source snapshot, engine inputs, versions, and witness semantics in these two isolated runs.",
    }
    chain = _with_hash(body, "chain_sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(chain, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return chain


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    emit = sub.add_parser("emit")
    emit.add_argument("--profile", required=True, choices=sorted(PROFILES))
    emit.add_argument("--source-sha", required=True)
    emit.add_argument("--run-id", required=True)
    emit.add_argument("--job", required=True)
    emit.add_argument("--raw-log", required=True, type=Path)
    emit.add_argument("--repo-root", default=Path("."), type=Path)
    emit.add_argument("--output", required=True, type=Path)

    bind = sub.add_parser("bind")
    bind.add_argument("--receipts-root", required=True, type=Path)
    bind.add_argument("--repo-root", default=Path("."), type=Path)
    bind.add_argument("--claims", required=True, type=Path)
    bind.add_argument("--source-sha", required=True)
    bind.add_argument("--output", required=True, type=Path)

    compare = sub.add_parser("compare")
    compare.add_argument("--first-binding", required=True, type=Path)
    compare.add_argument("--second-binding", required=True, type=Path)
    compare.add_argument("--source-sha", required=True)
    compare.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "emit":
        emit_receipt(
            args.profile,
            source_sha=args.source_sha,
            run_id=args.run_id,
            job=args.job,
            raw_log=args.raw_log,
            repo_root=args.repo_root,
            output_path=args.output,
        )
    elif args.command == "bind":
        bind_receipts(
            receipts_root=args.receipts_root,
            repo_root=args.repo_root,
            claims_path=args.claims,
            expected_source_sha=args.source_sha,
            output_path=args.output,
        )
    else:
        compare_bindings(
            first_path=args.first_binding,
            second_path=args.second_binding,
            expected_source_sha=args.source_sha,
            output_path=args.output,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
