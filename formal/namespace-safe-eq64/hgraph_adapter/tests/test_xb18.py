from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from hgraph import WiringError
from hgraph.test import eval_node

from hgraph_adapter.xb18 import (
    C1C11Evidence,
    IsoPolicy,
    IsomorphismRequest,
    IsomorphismVerdict,
    NamespaceSpec,
    xb18_semantic_firewall_isomorphism_gate,
)

IDENTITY = (0, 1, 2, 3, 4, 5)


def synthetic_request(
    *,
    permutation: tuple[int, ...] = IDENTITY,
    exact_mapping: tuple[int, ...] = IDENTITY,
) -> IsomorphismRequest:
    source = NamespaceSpec(
        namespace_id="SYNTHETIC_NAMESPACE_A",
        structural_class="B6_Q6",
        axes=("a0", "a1", "a2", "a3", "a4", "a5"),
        polarity=("protect",) * 6,
        claim_ceiling="SYNTHETIC_ONLY",
    )
    target = NamespaceSpec(
        namespace_id="SYNTHETIC_NAMESPACE_B",
        structural_class="B6_Q6",
        axes=("b0", "b1", "b2", "b3", "b4", "b5"),
        polarity=("protect",) * 6,
        claim_ceiling="SYNTHETIC_ONLY",
    )
    evidence = C1C11Evidence(
        criteria=("PASS",) * 11,
        axis_sources=IDENTITY,
        axis_targets=IDENTITY,
        exact_mapping=exact_mapping,
    )
    return IsomorphismRequest(
        source=source,
        target=target,
        evidence=evidence,
        permutation=permutation,
    )


def real_request_without_axis_evidence() -> IsomorphismRequest:
    source = NamespaceSpec(
        namespace_id="X_AIPRBG_6GATE_DIAGNOSTIC_V1",
        structural_class="B6_Q6",
        axes=("Authority", "Identity", "Provenance", "Runtime", "Readback", "Governance"),
        polarity=("protect",) * 6,
        claim_ceiling="AUDIT_DIAGNOSTIC_ONLY",
    )
    target = NamespaceSpec(
        namespace_id="ESS_EQ64_6D_KERNEL",
        structural_class="B6_Q6",
        axes=(
            "energy_load",
            "volatility",
            "coherence",
            "phase_stability",
            "transient_headroom",
            "lock_margin",
        ),
        polarity=("risk", "risk", "protect", "protect", "protect", "protect"),
        claim_ceiling="CANONICAL_STRUCTURAL_EQ64_REFERENCE",
    )
    criteria = (
        "PASS", "PASS", "PASS", "PASS", "PASS",
        "HOLD", "HOLD", "HOLD",
        "PASS", "PASS", "PASS",
    )
    return IsomorphismRequest(
        source=source,
        target=target,
        evidence=C1C11Evidence(
            criteria=criteria,
            axis_sources=(),
            axis_targets=(),
            exact_mapping=(),
        ),
        permutation=IDENTITY,
    )


class XB18HGraphContractTests(unittest.TestCase):
    def test_synthetic_exact_mapping_passes_without_runtime_bind(self) -> None:
        expected = IsomorphismVerdict(
            structural_status="PASS",
            semantic_status="PASS",
            claim_ceiling="SEMANTIC_EXACT",
            reason_codes=(),
            runtime_bind=False,
        )
        self.assertEqual(
            eval_node(
                xb18_semantic_firewall_isomorphism_gate,
                [synthetic_request()],
                policy=IsoPolicy.REFERENCE_ONLY,
            ),
            [expected],
        )

    def test_real_namespaces_without_c7_axis_evidence_hold(self) -> None:
        expected = IsomorphismVerdict(
            structural_status="PASS",
            semantic_status="HOLD",
            claim_ceiling="STRUCTURAL_ONLY",
            reason_codes=("NO_AXIS_LEVEL_EVIDENCE",),
            runtime_bind=False,
        )
        self.assertEqual(
            eval_node(
                xb18_semantic_firewall_isomorphism_gate,
                [real_request_without_axis_evidence()],
                policy=IsoPolicy.REFERENCE_ONLY,
            ),
            [expected],
        )

    def test_predeclared_mapping_conflict_denies(self) -> None:
        swapped = (1, 0, 2, 3, 4, 5)
        expected = IsomorphismVerdict(
            structural_status="PASS",
            semantic_status="DENY",
            claim_ceiling="STRUCTURAL_ONLY",
            reason_codes=("DENY_EXACT_MAPPING_CONFLICT",),
            runtime_bind=False,
        )
        self.assertEqual(
            eval_node(
                xb18_semantic_firewall_isomorphism_gate,
                [synthetic_request(permutation=swapped)],
                policy=IsoPolicy.REFERENCE_ONLY,
            ),
            [expected],
        )

    def test_runtime_bind_policy_has_no_matching_overload(self) -> None:
        with self.assertRaises(WiringError):
            eval_node(
                xb18_semantic_firewall_isomorphism_gate,
                [synthetic_request()],
                policy=IsoPolicy.RUNTIME_BIND,
            )


if __name__ == "__main__":
    unittest.main()
