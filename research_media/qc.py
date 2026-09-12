from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys


def run(cmd: list[str], *, capture_stderr: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if capture_stderr else None,
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: qc.py <final.mp4>")

    path = pathlib.Path(sys.argv[1])
    if not path.is_file() or path.stat().st_size < 100_000:
        raise AssertionError("final MP4 missing or unexpectedly small")

    probe = run([
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ])
    data = json.loads(probe.stdout)
    streams = data["streams"]

    video = next(s for s in streams if s.get("codec_type") == "video")
    audio = next(s for s in streams if s.get("codec_type") == "audio")
    subtitle = next(s for s in streams if s.get("codec_type") == "subtitle")

    assert video["codec_name"] == "h264", video
    assert int(video["width"]) == 1920, video
    assert int(video["height"]) == 1080, video
    assert video.get("pix_fmt") == "yuv420p", video
    assert video.get("r_frame_rate") == "30/1", video

    assert audio["codec_name"] == "aac", audio
    assert int(audio["sample_rate"]) == 48000, audio
    assert int(audio["channels"]) == 2, audio

    assert subtitle["codec_name"] == "mov_text", subtitle

    duration = float(data["format"]["duration"])
    assert 5.8 <= duration <= 6.3, duration

    # Full decode pass: fail on damaged packets/streams.
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
        check=True,
    )

    # Independent integrated-loudness readback.
    loud = run([
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-filter_complex",
        "ebur128=framelog=verbose",
        "-f",
        "null",
        "-",
    ], capture_stderr=True)
    matches = re.findall(r"I:\s+(-?\d+(?:\.\d+)?)\s+LUFS", loud.stderr or "")
    if not matches:
        raise AssertionError("could not read integrated loudness")
    integrated_lufs = float(matches[-1])
    assert -17.2 <= integrated_lufs <= -14.8, integrated_lufs

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sha_path = path.with_suffix(path.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {path.name}\n", encoding="utf-8")

    probe_path = path.with_suffix(path.suffix + ".ffprobe.json")
    probe_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    print(f"duration_seconds = {duration:.3f}")
    print(f"integrated_lufs = {integrated_lufs:.1f}")
    print(f"sha256 = {digest}")
    print("M4-F FINAL DELIVERY QC = PASS")


if __name__ == "__main__":
    main()
