from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hgraph import CompoundScalar, TS, compute_node, graph, operator

from reference.namespace_safe_engine import classify_mapping, validate_namespace


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


def _namespace_dict(spec: NamespaceSpec) -> dict:
    return {
        "namespace_id": spec.namespace_id,
        "structural_class": spec.structural_class,
        "axes": list(spec.axes),
        "polarity": list(spec.polarity),
        "claim_ceiling": spec.claim_ceiling,
    }


def _evidence_dict(evidence: C1C11Evidence) -> dict:
    criteria = {f"C{i + 1}": state for i, state in enumerate(evidence.criteria)}
    axis_equivalences = [
        {"source": source, "target": target}
        for source, target in zip(evidence.axis_sources, evidence.axis_targets)
    ]
    return {
        "criteria": criteria,
        "axis_equivalences": axis_equivalences,
        "exact_mapping": list(evidence.exact_mapping),
    }


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
    value = request.value
    source = _namespace_dict(value.source)
    target = _namespace_dict(value.target)
    validate_namespace(source)
    validate_namespace(target)
    result = classify_mapping(
        source,
        target,
        _evidence_dict(value.evidence),
        tuple(value.permutation),
    )
    return IsomorphismVerdict(
        structural_status=result["structural_status"].value,
        semantic_status=result["semantic_status"].value,
        claim_ceiling=result["claim_ceiling"],
        reason_codes=tuple(result["reason_codes"]),
        runtime_bind=False,
    )


@graph
def xb18_semantic_firewall_isomorphism_gate(
    request: TS[IsomorphismRequest], policy: IsoPolicy = IsoPolicy.REFERENCE_ONLY
) -> TS[IsomorphismVerdict]:
    """Shadow-only XB18 graph. No runtime/global bind is performed by this graph."""
    return verify_structural_isomorphism(request, policy)
