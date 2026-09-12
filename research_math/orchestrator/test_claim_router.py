from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "canary_claims.json"
ROUTER = HERE / "claim_router.py"


def run_router() -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROUTER), str(FIXTURE)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, (
        f"P3 router must execute successfully; rc={proc.returncode}; "
        f"stderr={proc.stderr.strip()!r}"
    )
    return json.loads(proc.stdout)


def by_id(report: dict) -> dict[str, dict]:
    return {item["id"]: item for item in report["claims"]}


def run() -> None:
    report = run_router()
    assert report["schema"] == "proofpath.math_claim_router.report.v1"
    claims = by_id(report)

    # P3 is a routing/admission-preparation layer only. It may never grant
    # mathematical PASS before downstream proof/quorum/receipt gates execute.
    assert all(item["status"] != "PASS" for item in claims.values())

    assert claims["ALG-1"]["status"] == "ROUTE_READY"
    assert claims["ALG-1"]["required_roles"] == [
        "exact_computation",
        "independent_exact_crosscheck",
    ]

    assert claims["NUM-1"]["status"] == "ROUTE_READY"
    assert claims["NUM-1"]["required_roles"] == [
        "numerical_computation",
        "independent_numeric_crosscheck",
    ]

    assert claims["RIG-1"]["status"] == "ROUTE_READY"
    assert claims["RIG-1"]["required_roles"] == [
        "rigorous_enclosure",
        "independent_crosscheck",
    ]

    assert claims["THM-1"]["status"] == "ROUTE_READY"
    assert claims["THM-1"]["required_roles"] == [
        "formal_kernel_proof",
        "independent_countercheck",
    ]

    assert claims["HPC-1"]["status"] == "ROUTE_READY"
    assert claims["HPC-1"]["required_roles"] == [
        "hpc_computation",
        "deterministic_independent_replay",
    ]

    assert claims["BAD-1"]["status"] == "HOLD_UNSUPPORTED_CLAIM_CLASS"
    assert claims["BAD-2"]["status"] == "HOLD_INCOMPLETE_CLAIM_SPEC"

    # The router exposes candidates, not proof authority. Downstream gates
    # must still verify that the requested roles were actually satisfied.
    assert "sage" in claims["ALG-1"]["engine_candidates"]["exact_computation"]
    assert "arb" in claims["RIG-1"]["engine_candidates"]["rigorous_enclosure"]
    assert "lean" in claims["THM-1"]["engine_candidates"]["formal_kernel_proof"]
    assert "julia" in claims["HPC-1"]["engine_candidates"]["hpc_computation"]

    print("P3 CLAIM AUTHORITY ROUTER CONTRACT = PASS")
    print("P3 FAIL-CLOSED UNKNOWN CLASS = PASS")
    print("P3 FAIL-CLOSED INCOMPLETE SPEC = PASS")
    print("P3 NO-PREMATURE-MATH-PASS INVARIANT = PASS")


if __name__ == "__main__":
    run()
