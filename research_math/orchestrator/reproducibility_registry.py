from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


POLICY_SCHEMA = "proofpath.reproducibility_policy.v1"
MANIFEST_SCHEMA = "proofpath.reproducibility_run_manifest.v1"
REGISTRY_SCHEMA = "proofpath.n_run_divergence_registry.v1"
BINDING_SCHEMA = "proofpath.live_engine_binding.v2"


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


def _decimal(value: Any, *, label: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label}: invalid decimal") from exc
    if not out.is_finite():
        raise ValueError(f"{label}: non-finite decimal")
    return out


def _decimal_text(value: Decimal) -> str:
    return str(value.normalize()) if value != 0 else "0"


def _validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("bad P13 policy schema")
    min_runs = policy.get("min_runs")
    if not isinstance(min_runs, int) or min_runs < 3:
        raise ValueError("P13 policy min_runs must be >= 3")
    claims = policy.get("claims")
    if not isinstance(claims, dict) or not claims:
        raise ValueError("P13 policy claims missing")
    for claim_id, spec in claims.items():
        if not isinstance(claim_id, str) or not isinstance(spec, dict):
            raise ValueError("P13 policy claim entry malformed")
        mode = spec.get("mode")
        if mode not in {"BIT_EXACT", "BOUNDED_NUMERIC"}:
            raise ValueError(f"{claim_id}: unsupported P13 mode")
        engines = spec.get("engines")
        if not isinstance(engines, list) or not engines or any(not isinstance(x, str) for x in engines):
            raise ValueError(f"{claim_id}: engine policy missing")
        metrics = spec.get("metrics", {})
        if mode == "BIT_EXACT" and metrics:
            raise ValueError(f"{claim_id}: BIT_EXACT cannot declare numeric metrics")
        if mode == "BOUNDED_NUMERIC":
            if not isinstance(metrics, dict) or not metrics:
                raise ValueError(f"{claim_id}: bounded numeric metrics missing")
            for metric_name, metric in metrics.items():
                if not isinstance(metric, dict):
                    raise ValueError(f"{claim_id}/{metric_name}: metric policy malformed")
                if metric.get("source_engine") not in engines:
                    raise ValueError(f"{claim_id}/{metric_name}: metric source engine not in claim engines")
                regex = metric.get("regex")
                if not isinstance(regex, str) or "(?P<value>" not in regex:
                    raise ValueError(f"{claim_id}/{metric_name}: metric regex must expose named value group")
                _decimal(metric.get("absolute_max"), label=f"{claim_id}/{metric_name}/absolute_max")
                _decimal(metric.get("max_spread"), label=f"{claim_id}/{metric_name}/max_spread")
    return policy


def _claim_statuses(binding: dict[str, Any]) -> dict[str, str]:
    try:
        claims = binding["assurance_bundle"]["gate"]["claims"]
    except (KeyError, TypeError) as exc:
        raise ValueError("binding missing claim gate") from exc
    return {str(item.get("id")): str(item.get("status")) for item in claims}


def _load_binding(path: Path, expected_source_sha: str) -> dict[str, Any]:
    binding = json.loads(path.read_text(encoding="utf-8"))
    if binding.get("schema") != BINDING_SCHEMA:
        raise ValueError(f"{path}: bad binding schema")
    if not _verify_hashed_record(binding, "binding_sha256"):
        raise ValueError(f"{path}: binding hash mismatch")
    if binding.get("source_sha") != expected_source_sha:
        raise ValueError(f"{path}: source SHA mismatch")
    run_id = binding.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError(f"{path}: missing run ID")
    identities = binding.get("engine_identity")
    if not isinstance(identities, dict) or not identities:
        raise ValueError(f"{path}: engine identity missing")
    statuses = _claim_statuses(binding)
    if not statuses or any(status != "PASS" for status in statuses.values()):
        raise ValueError(f"{path}: non-PASS claim state")
    claims_hash = binding.get("live_claims_sha256")
    if not isinstance(claims_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", claims_hash):
        raise ValueError(f"{path}: bad live claims hash")
    return binding


def _claim_fingerprint(binding: dict[str, Any], engines: list[str]) -> str:
    identities = binding["engine_identity"]
    missing = [engine for engine in engines if engine not in identities]
    if missing:
        raise ValueError(f"binding missing policy engines: {missing}")
    selected = {engine: deepcopy(identities[engine]) for engine in sorted(engines)}
    return _sha_obj(selected)


def build_run_manifest(
    *,
    binding_path: Path,
    expected_source_sha: str,
    policy: dict[str, Any],
    metric_logs: dict[str, Path],
    output_path: Path,
) -> dict[str, Any]:
    """Build one sealed P13 observation manifest from one already-verified P11 binding."""
    policy = _validate_policy(policy)
    binding = _load_binding(binding_path, expected_source_sha)
    statuses = _claim_statuses(binding)
    policy_claims = set(policy["claims"])
    if set(statuses) != policy_claims:
        raise ValueError("P13 policy/live claim set mismatch")

    observations: list[dict[str, Any]] = []
    used_logs: dict[str, str] = {}
    for claim_id in sorted(policy["claims"]):
        spec = policy["claims"][claim_id]
        item: dict[str, Any] = {
            "claim_id": claim_id,
            "mode": spec["mode"],
            "status": statuses[claim_id],
            "engines": sorted(spec["engines"]),
            "semantic_fingerprint_sha256": _claim_fingerprint(binding, spec["engines"]),
            "metrics": {},
        }
        for metric_name, metric_spec in sorted(spec.get("metrics", {}).items()):
            engine = metric_spec["source_engine"]
            log_path = metric_logs.get(engine)
            if log_path is None or not log_path.is_file():
                raise ValueError(f"{claim_id}/{metric_name}: metric log missing for {engine}")
            raw = log_path.read_text(encoding="utf-8")
            match = re.search(metric_spec["regex"], raw)
            if match is None:
                raise ValueError(f"{claim_id}/{metric_name}: metric observation missing")
            value = _decimal(match.group("value"), label=f"{claim_id}/{metric_name}/observed")
            item["metrics"][metric_name] = {
                "source_engine": engine,
                "value": _decimal_text(value),
            }
            used_logs[engine] = _sha_file(log_path)
        observations.append(item)

    body = {
        "schema": MANIFEST_SCHEMA,
        "status": "PASS",
        "source_sha": expected_source_sha,
        "run_id": binding["run_id"],
        "binding_sha256": binding["binding_sha256"],
        "live_claims_sha256": binding["live_claims_sha256"],
        "policy_sha256": _sha_obj(policy),
        "metric_log_sha256": dict(sorted(used_logs.items())),
        "claims": observations,
        "claim_ceiling": "P13 run manifest records one run only; cross-run reproducibility requires the N-run registry gate.",
    }
    manifest = _with_hash(body, "manifest_sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _load_manifest(path: Path, expected_source_sha: str, policy: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"{path}: bad P13 manifest schema")
    if not _verify_hashed_record(manifest, "manifest_sha256"):
        raise ValueError(f"{path}: manifest hash mismatch")
    if manifest.get("status") != "PASS":
        raise ValueError(f"{path}: non-PASS manifest")
    if manifest.get("source_sha") != expected_source_sha:
        raise ValueError(f"{path}: source SHA mismatch")
    if manifest.get("policy_sha256") != _sha_obj(policy):
        raise ValueError(f"{path}: policy hash mismatch")
    claims = manifest.get("claims")
    if not isinstance(claims, list):
        raise ValueError(f"{path}: claims missing")
    by_claim = {str(item.get("claim_id")): item for item in claims}
    if set(by_claim) != set(policy["claims"]):
        raise ValueError(f"{path}: claim set mismatch")
    return manifest


def _write_registry(body: dict[str, Any], output_path: Path) -> dict[str, Any]:
    registry = _with_hash(body, "registry_sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def build_n_run_registry(
    *,
    manifest_paths: list[Path],
    expected_source_sha: str,
    policy: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Build the fail-closed N-run reproducibility and divergence registry."""
    policy = _validate_policy(policy)
    manifests = [_load_manifest(path, expected_source_sha, policy) for path in manifest_paths]
    run_ids = [str(item.get("run_id", "")) for item in manifests]
    min_runs = int(policy["min_runs"])

    base = {
        "schema": REGISTRY_SCHEMA,
        "source_sha": expected_source_sha,
        "run_count": len(manifests),
        "run_ids": run_ids,
        "min_runs": min_runs,
        "policy_sha256": _sha_obj(policy),
        "manifest_sha256": [item["manifest_sha256"] for item in manifests],
        "claims": [],
        "claim_ceiling": "P13 covers only the configured live claims, exact source snapshot, declared engine identities, and explicit divergence policy across the recorded runs.",
    }

    if len(manifests) < min_runs:
        return _write_registry({**base, "status": "HOLD_INSUFFICIENT_RUNS"}, output_path)
    if any(not run_id for run_id in run_ids) or len(set(run_ids)) != len(run_ids):
        return _write_registry({**base, "status": "HOLD_DUPLICATE_RUN_ID"}, output_path)

    live_hashes = {str(item.get("live_claims_sha256")) for item in manifests}
    if len(live_hashes) != 1:
        return _write_registry({**base, "status": "HOLD_DIVERGENCE", "global_hold": "HOLD_LIVE_CLAIMS_DRIFT"}, output_path)
    base["live_claims_sha256"] = next(iter(live_hashes))

    manifest_claims = [
        {str(item["claim_id"]): item for item in manifest["claims"]}
        for manifest in manifests
    ]
    claim_results: list[dict[str, Any]] = []
    for claim_id in sorted(policy["claims"]):
        spec = policy["claims"][claim_id]
        observations = [claims[claim_id] for claims in manifest_claims]
        fingerprints = [str(item.get("semantic_fingerprint_sha256", "")) for item in observations]
        result: dict[str, Any] = {
            "claim_id": claim_id,
            "mode": spec["mode"],
            "engines": sorted(spec["engines"]),
            "semantic_variant_count": len(set(fingerprints)),
            "semantic_fingerprint_sha256": sorted(set(fingerprints)),
            "metrics": {},
            "status": "PASS",
        }
        if any(item.get("status") != "PASS" for item in observations):
            result["status"] = "HOLD_NON_PASS_INPUT"
        elif len(set(fingerprints)) != 1:
            result["status"] = "HOLD_EXACT_DIVERGENCE"

        if spec["mode"] == "BOUNDED_NUMERIC":
            for metric_name, metric_spec in sorted(spec["metrics"].items()):
                values: list[Decimal] = []
                metric_missing = False
                for item in observations:
                    metric = item.get("metrics", {}).get(metric_name)
                    if not isinstance(metric, dict) or "value" not in metric:
                        metric_missing = True
                        break
                    values.append(_decimal(metric["value"], label=f"{claim_id}/{metric_name}/manifest"))
                if metric_missing:
                    metric_result = {"status": "HOLD_METRIC_MISSING"}
                    result["status"] = "HOLD_TOLERANCE_EXCEEDED"
                else:
                    observed_min = min(values)
                    observed_max = max(values)
                    spread = observed_max - observed_min
                    absolute_max = _decimal(metric_spec["absolute_max"], label=f"{claim_id}/{metric_name}/absolute_max")
                    max_spread = _decimal(metric_spec["max_spread"], label=f"{claim_id}/{metric_name}/max_spread")
                    within_absolute = max(abs(value) for value in values) <= absolute_max
                    within_spread = spread <= max_spread
                    metric_status = "PASS" if within_absolute and within_spread else "HOLD_TOLERANCE_EXCEEDED"
                    metric_result = {
                        "status": metric_status,
                        "observed": [_decimal_text(value) for value in values],
                        "observed_min": _decimal_text(observed_min),
                        "observed_max": _decimal_text(observed_max),
                        "observed_spread": _decimal_text(spread),
                        "absolute_max": _decimal_text(absolute_max),
                        "max_spread": _decimal_text(max_spread),
                    }
                    if metric_status != "PASS":
                        result["status"] = "HOLD_TOLERANCE_EXCEEDED"
                result["metrics"][metric_name] = metric_result
        claim_results.append(result)

    status = "PASS" if all(item["status"] == "PASS" for item in claim_results) else "HOLD_DIVERGENCE"
    divergence_count = sum(item["status"] != "PASS" for item in claim_results)
    return _write_registry(
        {
            **base,
            "status": status,
            "divergence_count": divergence_count,
            "claims": claim_results,
        },
        output_path,
    )


def _load_policy(path: Path) -> dict[str, Any]:
    return _validate_policy(json.loads(path.read_text(encoding="utf-8")))


def _parse_metric_logs(items: list[str]) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for item in items:
        engine, sep, raw_path = item.partition("=")
        if not sep or not engine or not raw_path:
            raise ValueError("--metric-log must be ENGINE=PATH")
        if engine in out:
            raise ValueError(f"duplicate metric log engine: {engine}")
        out[engine] = Path(raw_path)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--binding", required=True, type=Path)
    manifest.add_argument("--source-sha", required=True)
    manifest.add_argument("--policy", required=True, type=Path)
    manifest.add_argument("--metric-log", action="append", default=[])
    manifest.add_argument("--output", required=True, type=Path)

    registry = sub.add_parser("registry")
    registry.add_argument("--manifest", action="append", required=True, type=Path)
    registry.add_argument("--source-sha", required=True)
    registry.add_argument("--policy", required=True, type=Path)
    registry.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()
    policy = _load_policy(args.policy)
    if args.command == "manifest":
        build_run_manifest(
            binding_path=args.binding,
            expected_source_sha=args.source_sha,
            policy=policy,
            metric_logs=_parse_metric_logs(args.metric_log),
            output_path=args.output,
        )
        return 0

    result = build_n_run_registry(
        manifest_paths=args.manifest,
        expected_source_sha=args.source_sha,
        policy=policy,
        output_path=args.output,
    )
    print(f"P13 N-RUN REGISTRY = {result['status']}")
    print(f"P13 RUN IDS = {result['run_ids']}")
    print(f"P13 REGISTRY SHA256 = {result['registry_sha256']}")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
