"""Shared validation and verdict structures."""

from __future__ import annotations

from typing import Any


def validate_bp(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer basis-point value")
    if value < 0 or value > 10000:
        raise ValueError(f"{field} must be in [0, 10000]")
    return value


def verdict_pass() -> dict:
    return {
        "verdict": "PASS",
        "reason_code": "PASS",
        "first_failed_guard": None,
        "failed_guards": [],
        "eligible_for_scoring": True,
    }


def verdict_hold(code: str, guard: str | None = None, failed_guards: list[str] | None = None) -> dict:
    failures = list(failed_guards) if failed_guards is not None else ([guard] if guard else [])
    return {
        "verdict": "HOLD",
        "reason_code": code,
        "first_failed_guard": guard,
        "failed_guards": failures,
        "eligible_for_scoring": False,
    }
