# Research Media Verification Stack

This directory defines a bounded, zero-spend media verification baseline for grant/application videos.

## Core gates

1. **M0-A — Media foundation**
   - exact FFmpeg static build asset
   - SHA-256 verified before use
   - `ffmpeg` + `ffprobe`
   - H.264 (`libx264`), AAC, and libass subtitle capability required

2. **M1-B — Render + edit**
   - generate a deterministic 1920x1080/30fps source
   - encode H.264/yuv420p + AAC/48kHz/stereo
   - perform a real two-segment trim + concat edit
   - duration readback

3. **M2-C — Audio**
   - apply EBU R128 loudness normalization toward -16 LUFS
   - preserve 48kHz stereo AAC
   - later QC independently measures integrated loudness

4. **M3-D — Captions/subtitles**
   - burn SRT captions into picture using libass
   - also mux a soft subtitle track (`mov_text`)
   - preserve the standalone `.srt`

5. **M4-F — Final delivery QC**
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

## Claim ceiling

A green CI run proves the implemented media pipeline can reproducibly create, edit, normalize, caption, package, and technically verify the bounded canary deliverable. It does **not** prove that every future video's narrative, aesthetics, factual content, accessibility, or competition-specific requirements are automatically correct. Those remain separate review gates.
