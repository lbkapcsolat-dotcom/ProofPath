#!/usr/bin/env python3
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: asr_compare.py EXPECTED.txt TRANSCRIPT.txt")

expected = Path(sys.argv[1]).read_text(encoding="utf-8")
actual = Path(sys.argv[2]).read_text(encoding="utf-8")

def norm(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())

exp = norm(expected)
act = norm(actual)
ratio = SequenceMatcher(a=exp, b=act).ratio()
required = {"proof", "path", "video", "publication"}
missing = sorted(required - set(act))
print("expected_words =", exp)
print("actual_words   =", act)
print(f"sequence_ratio = {ratio:.3f}")
print("missing_required =", missing)
assert ratio >= 0.80, ratio
assert not missing, missing
print("M5-A VOICE -> ASR TEXT FIDELITY = PASS")
