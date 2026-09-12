from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hgraph.test import eval_node

from hgraph_adapter.receipt import (
    build_shadow_receipt,
    canonical_json_bytes,
    write_shadow_receipt,
)
from hgraph_adapter.xb18 import (
    C1C11Evidence,
    IsoPolicy,
    IsomorphismRequest,
    NamespaceSpec,
    xb18_semantic_firewall_isomorphism_gate,
)

IDENTITY = (0, 1, 2, 3, 4, 5)


def _load_namespace(path: Path) -> NamespaceSpec:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return NamespaceSpec(
        namespace_id=raw["namespace_id"],
        structural_class=raw["structural_class"],
        axes=tuple(raw["axes"]),
        polarity=tuple(raw["polarity"]),
        claim_ceiling=raw["claim_ceiling"],
    )


def _write_json(path: Path, value: dict) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    source = _load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")
    target = _load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
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
    request = IsomorphismRequest(
        source=source,
        target=target,
        evidence=evidence,
        permutation=IDENTITY,
    )

    outputs = eval_node(
        xb18_semantic_firewall_isomorphism_gate,
        [request],
        policy=IsoPolicy.REFERENCE_ONLY,
    )
    if len(outputs) != 1 or outputs[0] is None:
        raise RuntimeError("XB18_EXPECTED_EXACTLY_ONE_VERDICT")
    verdict = outputs[0]
    if (
        verdict.structural_status != "PASS"
        or verdict.semantic_status != "HOLD"
        or verdict.claim_ceiling != "STRUCTURAL_ONLY"
        or verdict.runtime_bind is not False
    ):
        raise RuntimeError("XB18_REAL_NAMESPACE_FAIL_CLOSED_EXPECTATION_MISMATCH")

    request_payload = {
        "source_namespace": source.namespace_id,
        "target_namespace": target.namespace_id,
        "source": asdict(source),
        "target": asdict(target),
        "evidence": asdict(evidence),
        "permutation": list(IDENTITY),
        "policy": IsoPolicy.REFERENCE_ONLY.value,
    }
    verdict_payload = asdict(verdict)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    request_path = args.output_dir / "request.json"
    verdict_path = args.output_dir / "verdict.json"
    receipt_path = args.output_dir / "receipt.json"
    _write_json(request_path, request_payload)
    _write_json(verdict_path, verdict_payload)
    receipt = build_shadow_receipt(ROOT, request_payload, verdict_payload)
    write_shadow_receipt(receipt_path, receipt)

    print("PASS_XB18_SHADOW_RECEIPT_GENERATED")
    print(f"XB18_RECEIPT_PAYLOAD_SHA256={receipt['payload_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
