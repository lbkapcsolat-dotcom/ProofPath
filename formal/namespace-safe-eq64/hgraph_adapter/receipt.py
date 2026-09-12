from __future__ import annotations

from pathlib import Path
from typing import Any


SCHEMA_NAME = "HGRAPH_XB18_SHADOW_RECEIPT_V1"


def build_shadow_receipt(root: Path, request: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("XB18_RECEIPT_BUILDER_NOT_IMPLEMENTED")


def write_shadow_receipt(path: Path, receipt: dict[str, Any]) -> None:
    raise NotImplementedError("XB18_RECEIPT_WRITER_NOT_IMPLEMENTED")


def verify_shadow_receipt(
    root: Path,
    request: dict[str, Any],
    verdict: dict[str, Any],
    receipt_path: Path,
) -> dict[str, Any]:
    raise NotImplementedError("XB18_RECEIPT_VERIFIER_NOT_IMPLEMENTED")
