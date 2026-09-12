from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import live_evidence as live
import reproducibility_registry as p13


def expect_failure(fn, needle: str) -> None:
    try:
        fn()
    except ValueError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {needle!r}")


def binding(run_id: str, *, source_sha: str = "a" * 40, witness: str = "stable") -> dict:
    body = {
        "schema": "proofpath.live_engine_binding.v2",
        "source_sha": source_sha,
        "run_id": run_id,
        "live_claims_sha256": "b" * 64,
        "engine_identity": {
            "arb": {
                "engine_family": "flint_arb",
                "engine_version": "0.9.0",
                "input_sha256": {"arb.py": "1" * 64},
                "evidence_semantic_sha256": witness.ljust(64, "0")[:64],
                "adversarial_semantic_sha256": "2" * 64,
            },
            "julia": {
                "engine_family": "julia_runtime",
                "engine_version": "1.12.7",
                "input_sha256": {"julia.jl": "3" * 64},
                "evidence_semantic_sha256": "4" * 64,
                "adversarial_semantic_sha256": "5" * 64,
            },
            "lean": {
                "engine_family": "lean_kernel",
                "engine_version": "4.33.1",
                "input_sha256": {"proof.lean": "6" * 64},
                "evidence_semantic_sha256": "7" * 64,
                "adversarial_semantic_sha256": "8" * 64,
            },
            "sage": {
                "engine_family": "cas_sage",
                "engine_version": "10.9",
                "input_sha256": {"sage.py": "9" * 64},
                "evidence_semantic_sha256": "a" * 64,
                "adversarial_semantic_sha256": "c" * 64,
            },
        },
        "assurance_bundle": {
            "gate": {
                "claims": [
                    {"id": "ALG-LIVE", "status": "PASS"},
                    {"id": "THM-LIVE", "status": "PASS"},
                    {"id": "RIG-LIVE", "status": "PASS"},
                    {"id": "HPC-LIVE", "status": "PASS"},
                ]
            }
        },
        "claim_ceiling": "test",
    }
    body["binding_sha256"] = live._sha_obj(body)
    return body


P13_POLICY = {
    "schema": "proofpath.reproducibility_policy.v1",
    "min_runs": 3,
    "claims": {
        "ALG-LIVE": {"mode": "BIT_EXACT", "engines": ["julia", "sage"]},
        "THM-LIVE": {"mode": "BIT_EXACT", "engines": ["lean", "sage"]},
        "RIG-LIVE": {
            "mode": "BOUNDED_NUMERIC",
            "engines": ["arb", "sage"],
            "metrics": {
                "arb_residual_radius": {
                    "source_engine": "arb",
                    "regex": r"sqrt\(2\)\^2 - 2 enclosure: \[\+/- (?P<value>[0-9.]+e[-+][0-9]+)\]",
                    "absolute_max": "1e-70",
                    "max_spread": "1e-72",
                }
            },
        },
        "HPC-LIVE": {"mode": "BIT_EXACT", "engines": ["julia", "sage"]},
    },
}


def write_binding(root: Path, run_id: str, *, witness: str = "stable") -> Path:
    path = root / f"binding-{run_id}.json"
    path.write_text(json.dumps(binding(run_id, witness=witness)), encoding="utf-8")
    return path


def write_arb_log(root: Path, run_id: str, radius: str) -> Path:
    path = root / f"arb-{run_id}.log"
    path.write_text(
        "python-flint version: 0.9.0\n"
        f"sqrt(2)^2 - 2 enclosure: [+/- {radius}]\n"
        "PROOFPATH_EVIDENCE RIG-LIVE rigorous_enclosure residual_contains_zero=true\n",
        encoding="utf-8",
    )
    return path


def run_p13_contract() -> None:
    assert hasattr(p13, "build_run_manifest"), "P13 run manifest builder is missing"
    assert hasattr(p13, "build_n_run_registry"), "P13 N-run registry builder is missing"

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifests: list[Path] = []
        for run_id, radius in [("100", "1.23e-80"), ("200", "1.24e-80"), ("300", "1.22e-80")]:
            manifest_path = root / f"manifest-{run_id}.json"
            p13.build_run_manifest(
                binding_path=write_binding(root, run_id),
                expected_source_sha="a" * 40,
                policy=P13_POLICY,
                metric_logs={"arb": write_arb_log(root, run_id, radius)},
                output_path=manifest_path,
            )
            manifests.append(manifest_path)

        registry_path = root / "registry.json"
        registry = p13.build_n_run_registry(
            manifest_paths=manifests,
            expected_source_sha="a" * 40,
            policy=P13_POLICY,
            output_path=registry_path,
        )
        assert registry["status"] == "PASS"
        assert registry["run_count"] == 3
        assert len(set(registry["run_ids"])) == 3
        by_claim = {item["claim_id"]: item for item in registry["claims"]}
        assert by_claim["ALG-LIVE"]["mode"] == "BIT_EXACT"
        assert by_claim["ALG-LIVE"]["status"] == "PASS"
        assert by_claim["RIG-LIVE"]["mode"] == "BOUNDED_NUMERIC"
        assert by_claim["RIG-LIVE"]["status"] == "PASS"
        metric = by_claim["RIG-LIVE"]["metrics"]["arb_residual_radius"]
        assert metric["observed_min"] == "1.22E-80"
        assert metric["observed_max"] == "1.24E-80"
        assert metric["status"] == "PASS"
        assert registry_path.is_file()

        too_few = p13.build_n_run_registry(
            manifest_paths=manifests[:2],
            expected_source_sha="a" * 40,
            policy=P13_POLICY,
            output_path=root / "too-few.json",
        )
        assert too_few["status"] == "HOLD_INSUFFICIENT_RUNS"

        drift_binding = binding("300")
        drift_binding["engine_identity"]["julia"]["evidence_semantic_sha256"] = "d" * 64
        drift_binding.pop("binding_sha256")
        drift_binding["binding_sha256"] = live._sha_obj(drift_binding)
        drift_path = root / "binding-300-drift.json"
        drift_path.write_text(json.dumps(drift_binding), encoding="utf-8")
        drift_manifest = root / "manifest-300-drift.json"
        p13.build_run_manifest(
            binding_path=drift_path,
            expected_source_sha="a" * 40,
            policy=P13_POLICY,
            metric_logs={"arb": write_arb_log(root, "300-drift", "1.22e-80")},
            output_path=drift_manifest,
        )
        drift_registry = p13.build_n_run_registry(
            manifest_paths=[manifests[0], manifests[1], drift_manifest],
            expected_source_sha="a" * 40,
            policy=P13_POLICY,
            output_path=root / "drift-registry.json",
        )
        assert drift_registry["status"] == "HOLD_DIVERGENCE"
        drift_claims = {item["claim_id"]: item for item in drift_registry["claims"]}
        assert drift_claims["ALG-LIVE"]["status"] == "HOLD_EXACT_DIVERGENCE"
        assert drift_claims["HPC-LIVE"]["status"] == "HOLD_EXACT_DIVERGENCE"

        bad_metric_manifest = root / "manifest-300-bad-metric.json"
        p13.build_run_manifest(
            binding_path=write_binding(root, "301"),
            expected_source_sha="a" * 40,
            policy=P13_POLICY,
            metric_logs={"arb": write_arb_log(root, "301", "1.00e-60")},
            output_path=bad_metric_manifest,
        )
        bad_metric_registry = p13.build_n_run_registry(
            manifest_paths=[manifests[0], manifests[1], bad_metric_manifest],
            expected_source_sha="a" * 40,
            policy=P13_POLICY,
            output_path=root / "bad-metric-registry.json",
        )
        assert bad_metric_registry["status"] == "HOLD_DIVERGENCE"
        bad_claims = {item["claim_id"]: item for item in bad_metric_registry["claims"]}
        assert bad_claims["RIG-LIVE"]["status"] == "HOLD_TOLERANCE_EXCEEDED"

    print("P13 N>=3 DISTINCT RUN CONTRACT = PASS")
    print("P13 BIT-EXACT CLAIM POLICY = PASS")
    print("P13 BOUNDED NUMERIC TOLERANCE POLICY = PASS")
    print("P13 DIVERGENCE -> HOLD REGISTRY = PASS")


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first_path = root / "first.json"
        second_path = root / "second.json"
        output_path = root / "chain.json"

        first = binding("100")
        second = binding("200")
        first_path.write_text(json.dumps(first), encoding="utf-8")
        second_path.write_text(json.dumps(second), encoding="utf-8")

        chain = live.compare_bindings(
            first_path=first_path,
            second_path=second_path,
            expected_source_sha="a" * 40,
            output_path=output_path,
        )
        assert chain["status"] == "PASS"
        assert chain["run_ids"] == ["100", "200"]
        assert len(chain["chain_sha256"]) == 64
        assert output_path.is_file()

        same_run = binding("100")
        second_path.write_text(json.dumps(same_run), encoding="utf-8")
        expect_failure(
            lambda: live.compare_bindings(
                first_path=first_path,
                second_path=second_path,
                expected_source_sha="a" * 40,
                output_path=output_path,
            ),
            "replay run IDs must differ",
        )

        wrong_source = binding("200", source_sha="c" * 40)
        second_path.write_text(json.dumps(wrong_source), encoding="utf-8")
        expect_failure(
            lambda: live.compare_bindings(
                first_path=first_path,
                second_path=second_path,
                expected_source_sha="a" * 40,
                output_path=output_path,
            ),
            "source SHA mismatch",
        )

        drift = binding("200", witness="drift")
        second_path.write_text(json.dumps(drift), encoding="utf-8")
        expect_failure(
            lambda: live.compare_bindings(
                first_path=first_path,
                second_path=second_path,
                expected_source_sha="a" * 40,
                output_path=output_path,
            ),
            "engine identity drift",
        )

        tampered = copy.deepcopy(second)
        tampered["run_id"] = "201"
        second_path.write_text(json.dumps(tampered), encoding="utf-8")
        expect_failure(
            lambda: live.compare_bindings(
                first_path=first_path,
                second_path=second_path,
                expected_source_sha="a" * 40,
                output_path=output_path,
            ),
            "binding hash mismatch",
        )

    print("P12 DISTINCT RUN GUARD = PASS")
    print("P12 SOURCE SNAPSHOT GUARD = PASS")
    print("P12 ENGINE/WITNESS CONSISTENCY GUARD = PASS")
    print("P12 BINDING TAMPER GUARD = PASS")
    print("P12 CROSS-RUN RECEIPT CHAIN = PASS")
    run_p13_contract()


if __name__ == "__main__":
    run()
