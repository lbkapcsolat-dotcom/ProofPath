# ProofPath — Submission V1

ProofPath is an offline educational AI/ML prototype for learning evidence reasoning.

A learner provides a claim and evidence. ProofPath classifies the relationship as:
- SUPPORTED
- CONTRADICTED
- INSUFFICIENT

## ML
The app trains a three-class softmax-regression classifier from bundled labeled examples at startup.
The verdict is learned from weighted text-pair features, not hard-coded per example.

Feature families include lexical overlap, coverage, negation mismatch, numeric mismatch, antonym conflict, contradiction cues, uncertainty cues, overclaim cues, and evidence/claim length ratio.

No external API, CDN, account, paid credit, or model download is required.

## WebMCP Challenge delta
This repository existed before the WebMCP Challenge submission period. The WebMCP integration in `webmcp.js`, its contract test in `test-webmcp.mjs`, and the app wiring that registers the `analyze_evidence` tool were added after the submission period began on August 25, 2026.

When the browser exposes `document.modelContext.registerTool`, ProofPath registers one structured tool:

- `analyze_evidence`
  - input: `claim`, `evidence`
  - output: the same bounded educational result used by the visible UI
  - fail-closed behavior: missing claim/evidence returns `BLOCK`
  - claim ceiling remains `EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`

If WebMCP is unavailable, ProofPath still works as the original browser app; the adapter returns without changing normal UI behavior.

## Verified bundled benchmark
10/10 on the fixed untouched holdout/demo set.

This is a tiny curated educational benchmark, not evidence of general-world accuracy.

## Run
`python -m http.server 8000`
then open `http://localhost:8000`

## Test
`node tests.mjs`

WebMCP adapter contract:
`node test-webmcp.mjs`

## WebMCP test path
1. Run the app from a static host or local HTTP server.
2. Open it in ChatGPT's in-app browser, or Chrome 149+ with WebMCP testing enabled.
3. Inspect the registered tools and confirm `analyze_evidence` is present.
4. Call it with both `claim` and `evidence` and confirm the structured result matches the visible ProofPath behavior.
5. Call it with an empty claim or evidence and confirm the tool returns `BLOCK`.

## License
MIT. See `LICENSE`.

## Claim ceiling
EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY

Not a truth detector, scientific validator, medical/legal tool, or general automatic fact checker.
