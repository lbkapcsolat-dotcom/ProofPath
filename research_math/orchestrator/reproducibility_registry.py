from __future__ import annotations

from pathlib import Path
from typing import Any


def build_n_run_registry(
    *,
    binding_paths: list[Path],
    expected_source_sha: str,
    policy: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Fail closed until the P13 N-run policy contract is implemented."""
    raise ValueError("P13 N-run divergence policy not implemented")
