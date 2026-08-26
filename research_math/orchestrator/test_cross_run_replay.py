from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import live_evidence as live


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


if __name__ == "__main__":
    run()
