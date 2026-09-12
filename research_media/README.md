# Research Media Verification Stack

This directory defines a bounded, zero-spend media verification baseline for grant/application videos.

## Production contract

Every application video starts from one structured manifest rather than ad-hoc editing:

`APPLICATION BRIEF -> MANIFEST -> STORYBOARD/TIMING -> SCRIPT/CAPTIONS -> RENDER -> CUT -> AUDIO -> SUBTITLES -> FINAL QC -> EVIDENCE PACKAGE`

The manifest records the project identity, target, delivery profile, ordered scenes, caption timing, and required deliverables. The same timing source deterministically generates the SRT used by the render pipeline.

## Core gates

1. **M0-0 — Manifest / storyboard contract**
   - validate project identity and target
   - enforce a 1920x1080/30fps delivery profile
   - require ordered, unique, non-overlapping scene/caption intervals
   - require MP4, SRT, poster, SHA-256, and ffprobe evidence deliverables
   - generate SRT deterministically from the manifest and compare it with the frozen reference

2. **M0-A — Media foundation**
   - exact FFmpeg static build asset
   - SHA-256 verified before use
   - `ffmpeg` + `ffprobe`
   - H.264 (`libx264`), AAC, and libass subtitle capability required

3. **M1-B/M1-C — Render + edit**
   - generate a deterministic 1920x1080/30fps source
   - encode H.264/yuv420p + AAC/48kHz/stereo
   - perform a real two-segment trim + concat edit
   - duration readback

4. **M2-D — Audio**
   - apply EBU R128 loudness normalization toward -16 LUFS
   - preserve 48kHz stereo AAC
   - later QC independently measures integrated loudness

5. **M3-E/M3-F — Captions/subtitles**
   - burn generated SRT captions into picture using libass
   - also mux a soft subtitle track (`mov_text`)
   - preserve the standalone generated `.srt`

6. **M4-G — Final delivery QC**
   - verify codec, resolution, pixel format, frame rate, audio sample rate/channels, subtitle stream, and duration with `ffprobe`
   - full decode pass with zero media errors
   - independent EBU R128 loudness readback
   - poster frame extraction
   - SHA-256 + ffprobe JSON evidence

## Standard application-video profile

- Container: MP4
- Video: H.264, 1920x1080, 30 fps, yuv420p
- Audio: AAC, 48 kHz, stereo
- Loudness target: approximately -16 LUFS integrated
- Captions: burned-in for accessibility + soft subtitle track + separate SRT
- Integrity: full decode + SHA-256

## Optional local accelerators

These are not authority for the zero-spend CI baseline:

- **Genra** — local timeline/editor/render/export surface when its loopback API is reachable.
- **Yaps Auto Cut** — pause/dead-air removal when the local engine and eligible account are available.
- **Yaps Auto Captions / SRT / transcription** — local speech alignment and caption correction.
- **Yaps Audio Cleaner** — local denoise/enhancement.
- **Remotion** — optional higher-level programmatic scene/composition layer for richer production work.

A local accelerator may fail or be unavailable without invalidating the core render/edit/QC lane.

## Future per-video review gates

Technical PASS is necessary but not sufficient. Before a real submission, each video still needs separate review for:

- factual/source accuracy;
- competition-specific duration/file/branding rules;
- narrative clarity and pacing;
- visual hierarchy and legibility;
- caption correctness and accessibility;
- music/image/video licensing and attribution where applicable;
- final human visual/audio review of the rendered artifact.

## Claim ceiling

A green CI run proves the implemented media pipeline can reproducibly validate a manifest, generate caption timing, create, edit, normalize, caption, package, and technically verify the bounded canary deliverable. It does **not** prove that every future video's narrative, aesthetics, factual content, accessibility, or competition-specific requirements are automatically correct. Those remain separate review gates.
