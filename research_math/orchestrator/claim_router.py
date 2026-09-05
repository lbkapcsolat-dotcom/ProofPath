from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROUTING_POLICY: dict[str, dict[str, Any]] = {
    "exact_algebraic": {
        "required_roles": [
            "exact_computation",
            "independent_exact_crosscheck",
        ],
        "engine_candidates": {
            "exact_computation": ["sage", "wolfram", "python_exact"],
            "independent_exact_crosscheck": ["lean", "julia", "wolfram", "python_exact"],
        },
    },
    "numerical_approximation": {
        "required_roles": [
            "numerical_computation",
            "independent_numeric_crosscheck",
        ],
        "engine_candidates": {
            "numerical_computation": ["python", "julia", "wolfram"],
            "independent_numeric_crosscheck": ["precise", "julia", "wolfram"],
        },
    },
    "rigorous_numerical": {
        "required_roles": [
            "rigorous_enclosure",
            "independent_crosscheck",
        ],
        "engine_candidates": {
            "rigorous_enclosure": ["arb"],
            "independent_crosscheck": ["sage", "lean", "precise"],
        },
    },
    "theorem": {
        "required_roles": [
            "formal_kernel_proof",
            "independent_countercheck",
        ],
        "engine_candidates": {
            "formal_kernel_proof": ["lean"],
            "independent_countercheck": ["sage", "wolfram", "python"],
        },
    },
    "hpc_computation": {
        "required_roles": [
            "hpc_computation",
            "deterministic_independent_replay",
        ],
        "engine_candidates": {
            "hpc_computation": ["julia"],
            "deterministic_independent_replay": ["python", "sage"],
        },
    },
}


def _complete_spec(claim: dict[str, Any]) -> bool:
    required_keys = {"id", "text", "claim_class", "risk", "domain", "assumptions"}
    if not required_keys.issubset(claim):
        return False
    if not str(claim["id"]).strip():
        return False
    if not str(claim["text"]).strip():
        return False
    if not str(claim["domain"]).strip():
        return False
    if not isinstance(claim["assumptions"], list):
        return False
    return True


def route_claim(claim: dict[str, Any]) -> dict[str, Any]:
    claim_id = str(claim.get("id", ""))
    claim_class = str(claim.get("claim_class", ""))

    if claim_class not in ROUTING_POLICY:
        return {
            "id": claim_id,
            "claim_class": claim_class,
            "status": "HOLD_UNSUPPORTED_CLAIM_CLASS",
        }

    if not _complete_spec(claim):
        return {
            "id": claim_id,
            "claim_class": claim_class,
            "status": "HOLD_INCOMPLETE_CLAIM_SPEC",
        }

    policy = ROUTING_POLICY[claim_class]
    return {
        "id": claim_id,
        "claim_class": claim_class,
        "risk": claim["risk"],
        "domain": claim["domain"],
        "status": "ROUTE_READY",
        "required_roles": list(policy["required_roles"]),
        "engine_candidates": {
            role: list(candidates)
            for role, candidates in policy["engine_candidates"].items()
        },
        "claim_ceiling": "ROUTING_ONLY_NO_MATHEMATICAL_PASS",
    }


def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    claims = [route_claim(claim) for claim in payload.get("claims", [])]
    return {
        "schema": "proofpath.math_claim_router.report.v1",
        "input_schema": payload.get("schema"),
        "claim_count": len(claims),
        "routing_policy_classes": sorted(ROUTING_POLICY),
        "claims": claims,
        "claim_ceiling": (
            "P3 classifies claims and emits proof obligations only; "
            "it cannot grant mathematical PASS."
        ),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: claim_router.py <claims.json>", file=sys.stderr)
        return 2

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(build_report(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
