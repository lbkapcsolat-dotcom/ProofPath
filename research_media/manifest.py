from __future__ import annotations

import json
import pathlib
import sys


def srt_time(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("negative subtitle time")
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: manifest.py <manifest.json> <output.srt>")

    manifest_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert data["project_id"].strip()
    assert data["title"].strip()
    assert data["target"].strip()

    profile = data["profile"]
    assert profile == {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "max_duration_seconds": 180,
    }, profile

    scenes = data["scenes"]
    assert scenes, "at least one scene is required"
    ids: set[str] = set()
    previous_end = 0.0
    blocks: list[str] = []

    for index, scene in enumerate(scenes, start=1):
        scene_id = scene["id"].strip()
        assert scene_id and scene_id not in ids, scene_id
        ids.add(scene_id)

        start = float(scene["caption_start"])
        end = float(scene["caption_end"])
        caption = scene["caption"].strip()
        assert caption
        assert 0 <= start < end <= profile["max_duration_seconds"], scene
        assert start >= previous_end, "caption intervals must be ordered and non-overlapping"
        previous_end = end

        blocks.append(
            f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{caption}\n"
        )

    deliverables = data["deliverables"]
    required = {"mp4", "srt", "poster", "sha256", "ffprobe_json"}
    assert required.issubset(deliverables)
    assert all(deliverables[name] is True for name in required)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(blocks), encoding="utf-8")

    print(f"project_id = {data['project_id']}")
    print(f"scene_count = {len(scenes)}")
    print(f"last_caption_end = {previous_end:.3f}")
    print("M0-0 MANIFEST/STORYBOARD CONTRACT = PASS")


if __name__ == "__main__":
    main()
