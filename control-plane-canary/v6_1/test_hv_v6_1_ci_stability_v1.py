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
ROUNDS = 12


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


class RuntimeCIStabilityV1(unittest.TestCase):
    def test_repeated_cold_start_double_spend_exactly_one_winner(self):
        failures = []
        for i in range(ROUNDS):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                db = root / "hv_runtime.sqlite3"
                ctx = build_context(root, f"ci-stability-{i}")
                base = [sys.executable, str(WORKER), "resolve", "--db", str(db), "--context", str(ctx)]
                p1 = subprocess.Popen(base + ["--candidate", f"race-{i}-1"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p2 = subprocess.Popen(base + ["--candidate", f"race-{i}-2"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                        "round": i,
                        "p1_returncode": p1.returncode,
                        "p2_returncode": p2.returncode,
                        "p1_stdout": o1,
                        "p2_stdout": o2,
                        "p1_stderr": e1,
                        "p2_stderr": e2,
                        "r1": r1,
                        "r2": r2,
                    })
        self.assertEqual(failures, [], json.dumps(failures, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
