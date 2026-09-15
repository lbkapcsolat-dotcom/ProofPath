#!/usr/bin/env python3
from __future__ import annotations

import json
import pickle
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

WORKER = BASE / "hv_v6_1_restart_worker_v1.py"
WORKLOAD = b'{"action":"audit","target_system":"isolated_sandbox","payload":{"ci_stability":true}}'
BATCHES = 5
ROUNDS_PER_BATCH = 12
TOTAL_RACES = BATCHES * ROUNDS_PER_BATCH


def build_context(root: Path, nonce: str) -> Path:
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
    path = root / f"{nonce}.pkl"
    with path.open("wb") as f:
        pickle.dump(ctx, f)
    return path


def run_json(cmd: list[str]):
    cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
    line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "{}"
    try:
        out = json.loads(line)
    except json.JSONDecodeError:
        out = {}
    return cp, out


class RuntimeCIStabilityV1(unittest.TestCase):
    def test_repeated_initialized_runtime_double_spend_exactly_one_winner(self):
        failures = []
        observed = 0
        for batch in range(BATCHES):
            for round_in_batch in range(ROUNDS_PER_BATCH):
                observed += 1
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    db = root / "hv_runtime.sqlite3"
                    nonce = f"ci-stability-b{batch}-r{round_in_batch}"
                    ctx = build_context(root, nonce)

                    init_cmd = [sys.executable, str(WORKER), "snapshot", "--db", str(db)]
                    init_cp, init_out = run_json(init_cmd)
                    if init_cp.returncode != 0 or init_out.get("integrity_check") != "ok":
                        failures.append({
                            "batch": batch,
                            "round": round_in_batch,
                            "phase": "bootstrap",
                            "returncode": init_cp.returncode,
                            "stdout": init_cp.stdout,
                            "stderr": init_cp.stderr,
                            "result": init_out,
                        })
                        continue

                    base = [sys.executable, str(WORKER), "resolve", "--db", str(db), "--context", str(ctx)]
                    p1 = subprocess.Popen(base + ["--candidate", f"race-b{batch}-r{round_in_batch}-1"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p2 = subprocess.Popen(base + ["--candidate", f"race-b{batch}-r{round_in_batch}-2"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    o1, e1 = p1.communicate(timeout=30)
                    o2, e2 = p2.communicate(timeout=30)
                    try:
                        r1 = json.loads(o1.strip().splitlines()[-1]) if o1.strip() else {}
                        r2 = json.loads(o2.strip().splitlines()[-1]) if o2.strip() else {}
                    except json.JSONDecodeError:
                        r1, r2 = {}, {}
                    ok = (
                        p1.returncode == 0
                        and p2.returncode == 0
                        and sum(bool(x.get("executable")) for x in (r1, r2)) == 1
                        and (r2 if r1.get("executable") else r1).get("obligation") == "OBL-06"
                    )
                    if not ok:
                        failures.append({
                            "batch": batch,
                            "round": round_in_batch,
                            "phase": "double_spend",
                            "p1_returncode": p1.returncode,
                            "p2_returncode": p2.returncode,
                            "p1_stdout": o1,
                            "p2_stdout": o2,
                            "p1_stderr": e1,
                            "p2_stderr": e2,
                            "r1": r1,
                            "r2": r2,
                        })
        self.assertEqual(observed, TOTAL_RACES)
        self.assertEqual(failures, [], json.dumps(failures, sort_keys=True))
        print(json.dumps({
            "batches": BATCHES,
            "rounds_per_batch": ROUNDS_PER_BATCH,
            "total_races": observed,
            "exactly_one_winner": observed,
            "observed_flakes": 0,
            "scope": "INITIALIZED_HV_V6_1_RUNTIME_NONCE_RACE",
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
