from __future__ import annotations

from enum import Enum
import itertools
import json
from pathlib import Path

REGISTERED_NAMESPACES = {
    "ESS_EQ64_6D_KERNEL",
    "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
    "SYNTHETIC_NAMESPACE_A",
    "SYNTHETIC_NAMESPACE_B",
}


class Tri(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    DENY = "DENY"


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
