#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: normalize_narration.py INPUT_WAV OUTPUT_WAV")

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
assert src.exists() and src.stat().st_size > 0, src

pre = "aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur=6"
measure_filter = pre + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json"
measure = subprocess.run(
    ["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", measure_filter, "-t", "6", "-f", "null", "-"],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=True,
)
blocks = re.findall(r"\{\s*\"input_i\".*?\}", measure.stderr, re.S)
assert blocks, measure.stderr[-4000:]
m = json.loads(blocks[-1])

for key in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"):
    assert key in m, (key, m)

second = (
    pre
    + ",loudnorm=I=-16:TP=-1.5:LRA=11"
    + f":measured_I={m['input_i']}"
    + f":measured_TP={m['input_tp']}"
    + f":measured_LRA={m['input_lra']}"
    + f":measured_thresh={m['input_thresh']}"
    + f":offset={m['target_offset']}"
    + ":linear=true:print_format=summary"
)
subprocess.run(
    [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(src), "-af", second, "-t", "6",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(dst),
    ],
    check=True,
)
assert dst.exists() and dst.stat().st_size > 0, dst
print("measured_input_i =", m["input_i"])
print("measured_target_offset =", m["target_offset"])
print("M7-N TWO-PASS EBU R128 NARRATION = PASS")
