#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import hv_v6_1_runtime_enforcement_v1 as adapter


def load_context(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


def resolve(db: str, context_path: str, candidate: str, *, support_only: bool = False):
    ctx = load_context(context_path)
    ledger = adapter.HVRuntimeLedger.open_durable(db, adapter.ClaimLevel.LOCAL_TEST)
    try:
        req = adapter.RuntimeRequest(
            candidate_id=candidate,
            evidence_state="PROVEN_SUFFICIENT",
            authority_context=ctx,
            claim_level=adapter.ClaimLevel.LOCAL_TEST,
            support_only=support_only,
        )
        d = adapter.resolve_hv_runtime(
            req,
            ledger,
            current_edge_sha256=ctx["input_sha256"],
            current_state_sha256=ctx["raw_export_sha256"],
            current_policy_sha256=ctx["policy_sha256"],
        )
        return {"executable": d.executable, "verdict": d.verdict, "obligation": d.obligation, "reason": d.reason}
    finally:
        ledger.close()


def artifact_mint(artifact_path: str):
    raw = Path(artifact_path).read_bytes()
    artifact = json.loads(raw.decode("utf-8"))
    if not isinstance(artifact, dict):
        raise ValueError("ARTIFACT_OBJECT_REQUIRED")
    payload = artifact.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("ARTIFACT_PAYLOAD_OBJECT_REQUIRED")

    try:
        adapter.attempt_horizontal_mint_v(artifact)
    except PermissionError as e:
        if str(e) != "H_ONLY_CANNOT_MINT_V":
            raise
        return {
            "fresh_process_autoload": True,
            "inert_data_preserved": artifact.get("kind") == "DATA_ONLY",
            "artifact_sha256": hashlib.sha256(raw).hexdigest(),
            "artifact_schema": artifact.get("schema"),
            "marker": artifact.get("marker"),
            "payload_text": payload.get("text"),
            "payload_authority": payload.get("authority"),
            "authority_minted": False,
            "executable": False,
            "obligation": "OBL-17",
            "verdict": "REJECT_H_ONLY_CANNOT_MINT_V",
        }
    raise RuntimeError("H_ONLY_MINT_UNEXPECTEDLY_ALLOWED")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["resolve", "revoke", "snapshot", "artifact-mint"])
    ap.add_argument("--db", required=True)
    ap.add_argument("--context")
    ap.add_argument("--artifact")
    ap.add_argument("--candidate", default="restart-candidate")
    ap.add_argument("--support-only", action="store_true")
    args = ap.parse_args()
    try:
        if args.op == "resolve":
            if not args.context:
                raise ValueError("CONTEXT_REQUIRED")
            out = resolve(args.db, args.context, args.candidate, support_only=args.support_only)
        elif args.op == "revoke":
            if not args.context:
                raise ValueError("CONTEXT_REQUIRED")
            ctx = load_context(args.context)
            ledger = adapter.HVRuntimeLedger.open_durable(args.db, adapter.ClaimLevel.LOCAL_TEST)
            try:
                out = {"epoch": ledger.revoke(ctx)}
            finally:
                ledger.close()
        elif args.op == "artifact-mint":
            if not args.artifact:
                raise ValueError("ARTIFACT_REQUIRED")
            out = artifact_mint(args.artifact)
        else:
            ledger = adapter.HVRuntimeLedger.open_durable(args.db, adapter.ClaimLevel.LOCAL_TEST)
            try:
                out = ledger.durable_snapshot()
            finally:
                ledger.close()
        print(json.dumps(out, sort_keys=True))
        return 0
    except Exception as e:
        print(json.dumps({"error": type(e).__name__, "message": str(e)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
