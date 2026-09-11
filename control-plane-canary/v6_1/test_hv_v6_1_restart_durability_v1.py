#!/usr/bin/env python3
from __future__ import annotations

import json
import pickle
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import alpha_full_6d_local_control_plane_v6_1 as core
import hv_v6_1_runtime_enforcement_v1 as adapter

WORKER = BASE / "hv_v6_1_restart_worker_v1.py"
WORKLOAD = b'{"action":"audit","target_system":"isolated_sandbox","payload":{"restart":true}}'


class RestartDurabilityConformanceV1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "hv_runtime.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def context_file(self, nonce: str) -> Path:
        now = datetime.now(timezone.utc)
        keys = core.generate_role_keys()
        ctx = core.build_valid_context(
            role_keys=keys,
            workload_bytes=WORKLOAD,
            raw_export_sha256=core.sha256_bytes(("state:" + nonce).encode()),
            nonce=nonce,
            now=now,
            ttl_seconds=3600,
        )
        p = self.root / f"{nonce}.pkl"
        with p.open("wb") as f:
            pickle.dump(ctx, f)
        return p

    def run_worker(self, op: str, *, ctx: Path | None = None, candidate: str = "c", support_only: bool = False):
        cmd = [sys.executable, str(WORKER), op, "--db", str(self.db), "--candidate", candidate]
        if ctx is not None:
            cmd += ["--context", str(ctx)]
        if support_only:
            cmd.append("--support-only")
        cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
        line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "{}"
        return cp, json.loads(line)

    def test_01_replay_nonce_survives_fresh_process_restart(self):
        ctx = self.context_file("restart-replay")
        a, first = self.run_worker("resolve", ctx=ctx, candidate="replay-a")
        b, second = self.run_worker("resolve", ctx=ctx, candidate="replay-b")
        self.assertEqual(a.returncode, 0); self.assertTrue(first["executable"])
        self.assertEqual(b.returncode, 0); self.assertFalse(second["executable"])
        self.assertEqual(second["obligation"], "OBL-06")

    def test_02_revocation_survives_fresh_process_restart(self):
        ctx = self.context_file("restart-revoked")
        a, revoked = self.run_worker("revoke", ctx=ctx)
        b, decision = self.run_worker("resolve", ctx=ctx, candidate="revoked")
        self.assertEqual(a.returncode, 0); self.assertGreaterEqual(revoked["epoch"], 1)
        self.assertEqual(b.returncode, 0); self.assertFalse(decision["executable"])
        self.assertEqual(decision["obligation"], "OBL-08")

    def test_03_fresh_nonce_still_executes_after_restart(self):
        c1 = self.context_file("nonce-a"); c2 = self.context_file("nonce-b")
        _, first = self.run_worker("resolve", ctx=c1, candidate="a")
        _, second = self.run_worker("resolve", ctx=c2, candidate="b")
        self.assertTrue(first["executable"]); self.assertTrue(second["executable"])

    def test_04_revocation_epoch_is_monotonic_across_restart(self):
        c1 = self.context_file("rev-a"); c2 = self.context_file("rev-b")
        _, r1 = self.run_worker("revoke", ctx=c1)
        _, r2 = self.run_worker("revoke", ctx=c2)
        self.assertEqual(r2["epoch"], r1["epoch"] + 1)

    def test_05_concurrent_double_spend_exactly_one_executes(self):
        ctx = self.context_file("race-nonce")
        base = [sys.executable, str(WORKER), "resolve", "--db", str(self.db), "--context", str(ctx)]
        p1 = subprocess.Popen(base + ["--candidate", "race-1"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(base + ["--candidate", "race-2"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o1, _ = p1.communicate(timeout=30); o2, _ = p2.communicate(timeout=30)
        r1 = json.loads(o1.strip().splitlines()[-1]); r2 = json.loads(o2.strip().splitlines()[-1])
        self.assertEqual(p1.returncode, 0); self.assertEqual(p2.returncode, 0)
        self.assertEqual(sum(bool(x["executable"]) for x in (r1, r2)), 1)
        loser = r2 if r1["executable"] else r1
        self.assertEqual(loser["obligation"], "OBL-06")

    def test_06_distinct_nonces_do_not_cross_contaminate(self):
        c1 = self.context_file("distinct-a"); c2 = self.context_file("distinct-b")
        _, r1 = self.run_worker("resolve", ctx=c1, candidate="distinct-a")
        _, r2 = self.run_worker("resolve", ctx=c2, candidate="distinct-b")
        self.assertTrue(r1["executable"]); self.assertTrue(r2["executable"])

    def test_07_corrupt_database_fails_closed(self):
        self.db.write_bytes(b"NOT_A_SQLITE_DATABASE")
        cp, out = self.run_worker("snapshot")
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("DURABLE_STATE", out.get("message", ""))

    def test_08_schema_version_mismatch_fails_closed(self):
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO meta(key,value) VALUES('schema_version','999')")
        conn.commit(); conn.close()
        cp, out = self.run_worker("snapshot")
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("SCHEMA_VERSION", out.get("message", ""))

    def test_09_snapshot_reports_integrity_and_durable_counts(self):
        ctx = self.context_file("snapshot-nonce")
        _, r = self.run_worker("resolve", ctx=ctx, candidate="snapshot-candidate")
        self.assertTrue(r["executable"])
        cp, snap = self.run_worker("snapshot")
        self.assertEqual(cp.returncode, 0)
        self.assertEqual(snap["integrity_check"], "ok")
        self.assertEqual(snap["schema_version"], 1)
        self.assertGreaterEqual(snap["consumed_nonce_count"], 1)
        self.assertGreaterEqual(snap["candidate_count"], 1)

    def test_10_support_only_does_not_consume_nonce_across_restart(self):
        ctx = self.context_file("support-nonce")
        _, support = self.run_worker("resolve", ctx=ctx, candidate="support", support_only=True)
        _, real = self.run_worker("resolve", ctx=ctx, candidate="real")
        self.assertFalse(support["executable"])
        self.assertTrue(real["executable"])

    def test_11_candidate_record_survives_restart(self):
        ctx = self.context_file("candidate-nonce")
        self.run_worker("resolve", ctx=ctx, candidate="persistent-candidate", support_only=True)
        _, snap = self.run_worker("snapshot")
        self.assertGreaterEqual(snap["candidate_count"], 1)

    def test_12_legacy_in_memory_mode_remains_replay_safe(self):
        ctx_path = self.context_file("legacy-nonce")
        with ctx_path.open("rb") as f:
            ctx = pickle.load(f)
        ledger = adapter.HVRuntimeLedger(adapter.ClaimLevel.LOCAL_TEST)
        req = adapter.RuntimeRequest("legacy", "PROVEN_SUFFICIENT", ctx, adapter.ClaimLevel.LOCAL_TEST)
        kwargs = dict(current_edge_sha256=ctx["input_sha256"], current_state_sha256=ctx["raw_export_sha256"], current_policy_sha256=ctx["policy_sha256"])
        first = adapter.resolve_hv_runtime(req, ledger, **kwargs)
        second = adapter.resolve_hv_runtime(req, ledger, **kwargs)
        self.assertTrue(first.executable); self.assertFalse(second.executable)
        self.assertEqual(second.obligation, "OBL-06")


if __name__ == "__main__":
    unittest.main(verbosity=2)
