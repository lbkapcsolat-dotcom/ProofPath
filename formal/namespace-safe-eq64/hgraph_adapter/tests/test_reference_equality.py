from __future__ import annotations

import unittest

from hgraph.test import eval_node

from hgraph_adapter.xb18 import (
    C1C11Evidence,
    IsoPolicy,
    IsomorphismRequest,
    NamespaceSpec,
    xb18_semantic_firewall_isomorphism_gate,
)
from reference.namespace_safe_engine import classify_mapping

IDENTITY = (0, 1, 2, 3, 4, 5)


def ns(namespace_id: str, axes: tuple[str, ...], polarity: tuple[str, ...], ceiling: str) -> NamespaceSpec:
    return NamespaceSpec(
        namespace_id=namespace_id,
        structural_class="B6_Q6",
        axes=axes,
        polarity=polarity,
        claim_ceiling=ceiling,
    )


def direct_namespace(value: NamespaceSpec) -> dict:
    return {
        "namespace_id": value.namespace_id,
        "structural_class": value.structural_class,
        "axes": list(value.axes),
        "polarity": list(value.polarity),
        "claim_ceiling": value.claim_ceiling,
    }


def direct_evidence(value: C1C11Evidence) -> dict:
    return {
        "criteria": {f"C{i + 1}": state for i, state in enumerate(value.criteria)},
        "axis_equivalences": [
            {"source": source, "target": target}
            for source, target in zip(value.axis_sources, value.axis_targets)
        ],
        "exact_mapping": list(value.exact_mapping),
    }


def assert_reference_equals_hgraph(testcase: unittest.TestCase, request: IsomorphismRequest) -> None:
    direct = classify_mapping(
        direct_namespace(request.source),
        direct_namespace(request.target),
        direct_evidence(request.evidence),
        tuple(request.permutation),
    )
    outputs = eval_node(
        xb18_semantic_firewall_isomorphism_gate,
        [request],
        policy=IsoPolicy.REFERENCE_ONLY,
    )
    testcase.assertEqual(len(outputs), 1)
    actual = outputs[0]
    testcase.assertIsNotNone(actual)
    testcase.assertEqual(actual.structural_status, direct["structural_status"].value)
    testcase.assertEqual(actual.semantic_status, direct["semantic_status"].value)
    testcase.assertEqual(actual.claim_ceiling, direct["claim_ceiling"])
    testcase.assertEqual(actual.reason_codes, tuple(direct["reason_codes"]))
    testcase.assertFalse(actual.runtime_bind)


class ReferenceToHGraphEqualityMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.synthetic_a = ns(
            "SYNTHETIC_NAMESPACE_A",
            ("a0", "a1", "a2", "a3", "a4", "a5"),
            ("protect",) * 6,
            "SYNTHETIC_ONLY",
        )
        self.synthetic_b = ns(
            "SYNTHETIC_NAMESPACE_B",
            ("b0", "b1", "b2", "b3", "b4", "b5"),
            ("protect",) * 6,
            "SYNTHETIC_ONLY",
        )
        self.real_aiprbg = ns(
            "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
            ("Authority", "Identity", "Provenance", "Runtime", "Readback", "Governance"),
            ("protect",) * 6,
            "AUDIT_DIAGNOSTIC_ONLY",
        )
        self.real_ess = ns(
            "ESS_EQ64_6D_KERNEL",
            ("energy_load", "volatility", "coherence", "phase_stability", "transient_headroom", "lock_margin"),
            ("risk", "risk", "protect", "protect", "protect", "protect"),
            "CANONICAL_STRUCTURAL_EQ64_REFERENCE",
        )

    def test_exact_synthetic_pass_equality(self) -> None:
        evidence = C1C11Evidence(
            criteria=("PASS",) * 11,
            axis_sources=IDENTITY,
            axis_targets=IDENTITY,
            exact_mapping=IDENTITY,
        )
        assert_reference_equals_hgraph(
            self,
            IsomorphismRequest(self.synthetic_a, self.synthetic_b, evidence, IDENTITY),
        )

    def test_real_namespaces_missing_c7_hold_equality(self) -> None:
        criteria = (
            "PASS", "PASS", "PASS", "PASS", "PASS",
            "HOLD", "HOLD", "HOLD",
            "PASS", "PASS", "PASS",
        )
        evidence = C1C11Evidence(
            criteria=criteria,
            axis_sources=(),
            axis_targets=(),
            exact_mapping=(),
        )
        assert_reference_equals_hgraph(
            self,
            IsomorphismRequest(self.real_aiprbg, self.real_ess, evidence, IDENTITY),
        )

    def test_predeclared_mapping_conflict_deny_equality(self) -> None:
        evidence = C1C11Evidence(
            criteria=("PASS",) * 11,
            axis_sources=IDENTITY,
            axis_targets=IDENTITY,
            exact_mapping=(1, 0, 2, 3, 4, 5),
        )
        assert_reference_equals_hgraph(
            self,
            IsomorphismRequest(self.synthetic_a, self.synthetic_b, evidence, IDENTITY),
        )

    def test_criterion_deny_reason_code_equality(self) -> None:
        criteria = list(("PASS",) * 11)
        criteria[3] = "DENY"
        evidence = C1C11Evidence(
            criteria=tuple(criteria),
            axis_sources=IDENTITY,
            axis_targets=IDENTITY,
            exact_mapping=IDENTITY,
        )
        assert_reference_equals_hgraph(
            self,
            IsomorphismRequest(self.synthetic_a, self.synthetic_b, evidence, IDENTITY),
        )


if __name__ == "__main__":
    unittest.main()
