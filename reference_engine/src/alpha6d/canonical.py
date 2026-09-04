"""Deterministic canonical JSON and SHA256 helpers for ALPHA FULL 6D."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize(value: Any) -> Any:
    if isinstance(value, float):
        raise TypeError("floating-point values are not allowed in canonical decision objects")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("canonical JSON object keys must be strings")
        return {key: canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (set, frozenset)):
        items = [canonicalize(item) for item in value]
        return sorted(items, key=lambda item: canonical_json_bytes(item))
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    normalized = canonicalize(value)
    text = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
