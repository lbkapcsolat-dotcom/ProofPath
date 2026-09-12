from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from hgraph.test import eval_node

from hgraph_adapter.xb18 import (
    C1C11Evidence,
    IsoPolicy,
    IsomorphismRequest,
    IsomorphismVerdict,
    NamespaceSpec,
    xb18_semantic_firewall_isomorphism_gate,
)


def synthetic_request() -> IsomorphismRequest:
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
    identity = (0, 1, 2, 3, 4, 5)
    evidence = C1C11Evidence(
        criteria=("PASS",) * 11,
        axis_sources=identity,
        axis_targets=identity,
        exact_mapping=identity,
    )
    return IsomorphismRequest(
        source=source,
        target=target,
        evidence=evidence,
        permutation=identity,
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


if __name__ == "__main__":
    unittest.main()
