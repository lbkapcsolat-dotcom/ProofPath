#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

if len(sys.argv) != 5:
    raise SystemExit("usage: publication_package.py VIDEO SRT POSTER METADATA_JSON")

video, srt, poster, metadata_path = map(Path, sys.argv[1:])
for p in (video, srt, poster, metadata_path):
    assert p.exists() and p.stat().st_size > 0, p

metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
required = ["platform", "title", "description", "visibility", "language", "made_for_kids"]
for key in required:
    assert key in metadata, key
assert metadata["platform"] == "youtube"
assert metadata["visibility"] in {"private", "unlisted", "public"}
assert isinstance(metadata["made_for_kids"], bool)

sha = hashlib.sha256(video.read_bytes()).hexdigest()
package = {
    "status": "READY_FOR_MANUAL_UPLOAD",
    "video": str(video),
    "video_sha256": sha,
    "captions": str(srt),
    "poster": str(poster),
    "metadata": metadata,
    "remote_readback": {
        "status": "HOLD_PENDING_UPLOAD",
        "youtube_video_id": None,
        "youtube_url": None,
        "remote_title_match": None,
        "remote_duration_seconds": None,
        "remote_caption_readback": None,
        "remote_visibility": None
    }
}
out = video.parent / "publication-package.json"
out.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("publication_video_sha256 =", sha)
print("remote_readback = HOLD_PENDING_UPLOAD")
print("M8-P YOUTUBE PUBLICATION PACKAGE = PASS")
