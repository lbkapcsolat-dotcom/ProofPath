#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: normalize_remotion.py INPUT OUTPUT")

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
assert src.exists() and src.stat().st_size > 0, src

cmd = [
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-i", str(src),
    "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
    "-pix_fmt", "yuv420p", "-color_range", "tv",
    "-an", "-movflags", "+faststart",
    str(dst),
]
subprocess.run(cmd, check=True)
assert dst.exists() and dst.stat().st_size > 0, dst
print("M6-N REMOTION DELIVERY NORMALIZATION = PASS")
