from __future__ import annotations

import itertools

from namespace_safe_engine import Tri, classify_mapping


def run_canary(source: dict, target: dict, evidence: dict) -> dict:
    results = []
    for permutation in itertools.permutations(range(6)):
        classified = classify_mapping(source, target, evidence, permutation)
        results.append(
            {
                "permutation": list(permutation),
                "structural_status": classified["structural_status"].value,
                "semantic_status": classified["semantic_status"].value,
                "reason_codes": classified["reason_codes"],
            }
        )

    structural_pass = sum(
        row["structural_status"] == Tri.PASS.value for row in results
    )
    semantic_pass_rows = [
        row for row in results if row["semantic_status"] == Tri.PASS.value
    ]
    semantic_hold = sum(row["semantic_status"] == Tri.HOLD.value for row in results)
    semantic_deny = sum(row["semantic_status"] == Tri.DENY.value for row in results)

    return {
        "permutation_count": len(results),
        "structural_pass": structural_pass,
        "semantic_pass": len(semantic_pass_rows),
        "semantic_hold": semantic_hold,
        "semantic_deny": semantic_deny,
        "semantic_pass_permutations": [
            row["permutation"] for row in semantic_pass_rows
        ],
        "results": results,
    }


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    from namespace_safe_engine import load_namespace
    from receipt import build_receipt, write_canonical_json, write_receipt

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--result-out", type=Path, required=True)
    parser.add_argument("--receipt-out", type=Path, required=True)
    args = parser.parse_args()

    source = load_namespace(args.source)
    target = load_namespace(args.target)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = run_canary(source, target, evidence)
    write_canonical_json(args.result_out, result)
    receipt = build_receipt(args.root, args.source, args.target, args.evidence, args.result_out)
    write_receipt(args.receipt_out, receipt)
    print(json.dumps(receipt, sort_keys=True))
