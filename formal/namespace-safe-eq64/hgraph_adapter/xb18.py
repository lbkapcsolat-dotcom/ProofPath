from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hgraph import CompoundScalar, TS, compute_node, graph, operator


class IsoPolicy(str, Enum):
    REFERENCE_ONLY = "REFERENCE_ONLY"
    RUNTIME_BIND = "RUNTIME_BIND"


@dataclass(frozen=True)
class NamespaceSpec(CompoundScalar):
    namespace_id: str
    structural_class: str
    axes: tuple[str, ...]
    polarity: tuple[str, ...]
    claim_ceiling: str


@dataclass(frozen=True)
class C1C11Evidence(CompoundScalar):
    criteria: tuple[str, ...]
    axis_sources: tuple[int, ...]
    axis_targets: tuple[int, ...]
    exact_mapping: tuple[int, ...]


@dataclass(frozen=True)
class IsomorphismRequest(CompoundScalar):
    source: NamespaceSpec
    target: NamespaceSpec
    evidence: C1C11Evidence
    permutation: tuple[int, ...]


@dataclass(frozen=True)
class IsomorphismVerdict(CompoundScalar):
    structural_status: str
    semantic_status: str
    claim_ceiling: str
    reason_codes: tuple[str, ...]
    runtime_bind: bool


@operator
def verify_structural_isomorphism(
    request: TS[IsomorphismRequest], policy: IsoPolicy
) -> TS[IsomorphismVerdict]:
    """Verify a typed namespace-safe structural mapping under a wiring-time policy."""
    ...


@compute_node(
    overloads=verify_structural_isomorphism,
    requires=lambda m, policy: policy is IsoPolicy.REFERENCE_ONLY,
)
def verify_structural_isomorphism_reference(
    request: TS[IsomorphismRequest], policy: IsoPolicy
) -> TS[IsomorphismVerdict]:
    raise NotImplementedError("XB18_REFERENCE_VERIFIER_NOT_IMPLEMENTED")


@graph
def xb18_semantic_firewall_isomorphism_gate(
    request: TS[IsomorphismRequest], policy: IsoPolicy = IsoPolicy.REFERENCE_ONLY
) -> TS[IsomorphismVerdict]:
    """Shadow-only XB18 graph. No runtime/global bind is performed by this graph."""
    return verify_structural_isomorphism(request, policy)
