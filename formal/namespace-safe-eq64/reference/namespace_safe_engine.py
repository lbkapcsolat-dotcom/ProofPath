from __future__ import annotations

from enum import Enum
import hashlib
import itertools
import json
from pathlib import Path

CANONICAL_NAMESPACE_SPECS = {
    "ESS_EQ64_6D_KERNEL": {
        "namespace_id": "ESS_EQ64_6D_KERNEL",
        "structural_class": "B6_Q6",
        "axes": ["energy_load", "volatility", "coherence", "phase_stability", "transient_headroom", "lock_margin"],
        "polarity": ["risk", "risk", "protect", "protect", "protect", "protect"],
        "claim_ceiling": "CANONICAL_STRUCTURAL_EQ64_REFERENCE",
    },
    "X_AIPRBG_6GATE_DIAGNOSTIC_V1": {
        "namespace_id": "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
        "structural_class": "B6_Q6",
        "axes": ["Authority", "Identity", "Provenance", "Runtime", "Readback", "Governance"],
        "polarity": ["protect", "protect", "protect", "protect", "protect", "protect"],
        "claim_ceiling": "AUDIT_DIAGNOSTIC_ONLY",
    },
    "SYNTHETIC_NAMESPACE_A": {
        "namespace_id": "SYNTHETIC_NAMESPACE_A",
        "structural_class": "B6_Q6",
        "axes": ["a0", "a1", "a2", "a3", "a4", "a5"],
        "polarity": ["protect", "protect", "protect", "protect", "protect", "protect"],
        "claim_ceiling": "SYNTHETIC_TEST_ONLY",
    },
    "SYNTHETIC_NAMESPACE_B": {
        "namespace_id": "SYNTHETIC_NAMESPACE_B",
        "structural_class": "B6_Q6",
        "axes": ["b0", "b1", "b2", "b3", "b4", "b5"],
        "polarity": ["protect", "protect", "protect", "protect", "protect", "protect"],
        "claim_ceiling": "SYNTHETIC_TEST_ONLY",
    },
}
REGISTERED_NAMESPACES = set(CANONICAL_NAMESPACE_SPECS)


class Tri(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    DENY = "DENY"


def _canonical_json_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_namespace_digest(ns: dict) -> str:
    return hashlib.sha256(_canonical_json_bytes(ns)).hexdigest()


CANONICAL_NAMESPACE_DIGESTS = {
    namespace_id: canonical_namespace_digest(spec)
    for namespace_id, spec in CANONICAL_NAMESPACE_SPECS.items()
}


def load_namespace(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_namespace(ns: dict) -> None:
    required = {"namespace_id", "structural_class", "axes", "polarity", "claim_ceiling"}
    if set(ns) != required:
        raise ValueError("NAMESPACE_FIELDS_MISMATCH")
    if ns["structural_class"] != "B6_Q6":
        raise ValueError("UNSUPPORTED_STRUCTURAL_CLASS")
    if len(ns["axes"]) != 6 or len(set(ns["axes"])) != 6:
        raise ValueError("AXIS_SCHEMA_NOT_EXACT_6_UNIQUE")
    if len(ns["polarity"]) != 6 or any(
        polarity not in {"risk", "protect", "neutral"} for polarity in ns["polarity"]
    ):
        raise ValueError("POLARITY_SCHEMA_INVALID")


def canonical_namespace_matches_registry(ns: dict) -> bool:
    namespace_id = ns.get("namespace_id")
    if namespace_id not in REGISTERED_NAMESPACES:
        return False
    try:
        validate_namespace(ns)
    except (TypeError, ValueError, KeyError):
        return False
    return canonical_namespace_digest(ns) == CANONICAL_NAMESPACE_DIGESTS[namespace_id]


def all_states() -> list[tuple[int, ...]]:
    return list(itertools.product((0, 1), repeat=6))


def encode_state(state: tuple[int, ...]) -> int:
    if len(state) != 6 or any(bit not in (0, 1) for bit in state):
        raise ValueError("STATE_NOT_B6")
    return sum(bit << i for i, bit in enumerate(state))


def decode_state(value: int) -> tuple[int, ...]:
    if value < 0 or value >= 64:
        raise ValueError("STATE_ID_OUT_OF_RANGE")
    return tuple((value >> i) & 1 for i in range(6))


def normalize_polarity(ns: dict, state: tuple[int, ...]) -> tuple[int, ...]:
    validate_namespace(ns)
    if len(state) != 6 or any(bit not in (0, 1) for bit in state):
        raise ValueError("STATE_NOT_B6")
    return tuple(
        (1 - bit) if polarity == "risk" else bit
        for bit, polarity in zip(state, ns["polarity"])
    )


def _validate_permutation(permutation: tuple[int, ...]) -> None:
    if len(permutation) != 6 or set(permutation) != set(range(6)):
        raise ValueError("INVALID_PERMUTATION")


def apply_permutation(
    state: tuple[int, ...], permutation: tuple[int, ...]
) -> tuple[int, ...]:
    _validate_permutation(permutation)
    return tuple(state[i] for i in permutation)


def meet(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(x & y for x, y in zip(a, b))


def join(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(x | y for x, y in zip(a, b))


def hamming_distance(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return sum(x != y for x, y in zip(a, b))


def check_structural_mapping(permutation: tuple[int, ...]) -> dict:
    _validate_permutation(permutation)
    states = all_states()
    meet_ok = True
    join_ok = True
    hamming_ok = True
    for a in states:
        pa = apply_permutation(a, permutation)
        for b in states:
            pb = apply_permutation(b, permutation)
            meet_ok &= apply_permutation(meet(a, b), permutation) == meet(pa, pb)
            join_ok &= apply_permutation(join(a, b), permutation) == join(pa, pb)
            hamming_ok &= hamming_distance(a, b) == hamming_distance(pa, pb)
    return {
        "meet_preserved": bool(meet_ok),
        "join_preserved": bool(join_ok),
        "hamming_preserved": bool(hamming_ok),
    }


def _criterion_reason(key: str) -> str:
    return {
        "C4": "POLARITY_CONFLICT",
        "C5": "ALIAS_CONFLICT",
        "C9": "POST_HOC_SELECTION",
    }.get(key, f"CRITERION_DENY_{key}")


def _axis_mapping(axis_equivalences: list[dict]) -> tuple[int, ...] | None:
    if len(axis_equivalences) != 6:
        return None
    pairs = {(item.get("source"), item.get("target")) for item in axis_equivalences}
    if len(pairs) != 6:
        return None
    sources = {source for source, _ in pairs}
    targets = {target for _, target in pairs}
    if sources != set(range(6)) or targets != set(range(6)):
        return None
    by_source = dict(pairs)
    return tuple(by_source[i] for i in range(6))


def _axis_evidence_reference_error(axis_equivalences: list[dict]) -> str | None:
    refs: list[str] = []
    for item in axis_equivalences:
        ref = item.get("evidence_id")
        if not isinstance(ref, str) or not ref.strip():
            return "C7_EVIDENCE_REFERENCE_INVALID"
        refs.append(ref.strip())
    if len(set(refs)) != len(refs):
        return "C7_EVIDENCE_REFERENCE_NOT_INDEPENDENT"
    return None


def check_semantic_crosswalk(
    source: dict,
    target: dict,
    evidence: dict,
    permutation: tuple[int, ...],
) -> dict:
    _validate_permutation(permutation)
    source_id = source.get("namespace_id")
    target_id = target.get("namespace_id")

    if source_id == "EQ64" or target_id == "EQ64":
        return {
            "status": Tri.DENY,
            "reason_codes": ["DENY_POLICY_BARE_EQ64_FORBIDDEN"],
        }
    if source_id not in REGISTERED_NAMESPACES or target_id not in REGISTERED_NAMESPACES:
        return {"status": Tri.HOLD, "reason_codes": ["UNREGISTERED_NAMESPACE"]}
    if not canonical_namespace_matches_registry(source) or not canonical_namespace_matches_registry(target):
        return {"status": Tri.DENY, "reason_codes": ["REGISTERED_NAMESPACE_SCHEMA_MISMATCH"]}

    criteria = evidence.get("criteria", {})
    required = [f"C{i}" for i in range(1, 12)]
    if set(criteria) != set(required):
        return {"status": Tri.HOLD, "reason_codes": ["INCOMPLETE_C1_C11_EVIDENCE"]}
    if any(criteria[key] not in {"PASS", "HOLD", "DENY"} for key in required):
        return {"status": Tri.DENY, "reason_codes": ["INVALID_CRITERION_STATE"]}

    denied = [key for key in required if criteria[key] == "DENY"]
    if denied:
        return {"status": Tri.DENY, "reason_codes": [_criterion_reason(denied[0])]}

    axis_equivalences = evidence.get("axis_equivalences", [])
    derived_mapping = _axis_mapping(axis_equivalences)
    if criteria["C7"] != "PASS" or derived_mapping is None:
        return {"status": Tri.HOLD, "reason_codes": ["NO_AXIS_LEVEL_EVIDENCE"]}

    c7_error = _axis_evidence_reference_error(axis_equivalences)
    if c7_error is not None:
        return {"status": Tri.DENY, "reason_codes": [c7_error]}

    if any(criteria[key] != "PASS" for key in required):
        return {"status": Tri.HOLD, "reason_codes": ["INCOMPLETE_C1_C11_EVIDENCE"]}

    exact = evidence.get("exact_mapping")
    if exact is None:
        return {"status": Tri.HOLD, "reason_codes": ["NO_PREDECLARED_EXACT_MAPPING"]}
    exact_tuple = tuple(exact)
    if derived_mapping != exact_tuple:
        return {"status": Tri.DENY, "reason_codes": ["EVIDENCE_MAPPING_CONFLICT"]}
    if exact_tuple != permutation:
        return {"status": Tri.DENY, "reason_codes": ["DENY_EXACT_MAPPING_CONFLICT"]}
    return {"status": Tri.PASS, "reason_codes": []}


def classify_mapping(
    source: dict,
    target: dict,
    evidence: dict,
    permutation: tuple[int, ...],
) -> dict:
    structural = check_structural_mapping(permutation)
    semantic = check_semantic_crosswalk(source, target, evidence, permutation)
    structural_pass = all(structural.values())
    return {
        "structural_status": Tri.PASS if structural_pass else Tri.DENY,
        "semantic_status": semantic["status"],
        "claim_ceiling": (
            "SEMANTIC_EXACT" if semantic["status"] is Tri.PASS else "STRUCTURAL_ONLY"
        ),
        "reason_codes": semantic["reason_codes"],
    }
