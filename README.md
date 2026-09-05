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

## Verified bundled benchmark
10/10 on the fixed untouched holdout/demo set.

This is a tiny curated educational benchmark, not evidence of general-world accuracy.

## WebMCP Challenge delta — added after 2026-08-25

The pre-existing ProofPath UI remains intact. The challenge branch adds a bounded WebMCP adapter that exposes the same evidence-analysis path to compatible agents through:

`document.modelContext.registerTool(...)`

Registered tool: `analyze_evidence`

Inputs:
- `claim` — claim to assess
- `evidence` — evidence supplied for that claim

The tool calls the same `analyze()` function used by the human-facing UI. Missing claim or evidence remains fail-closed as `BLOCK`. The claim ceiling remains `EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`.

Challenge-specific additions:
- `webmcp.js` — WebMCP registration adapter
- `test-webmcp.mjs` — adapter contract and fail-closed tests
- `.github/workflows/webmcp-regression.yml` — full branch regression CI
- `LICENSE` — MIT open-source license

Temporary zero-cost live deployment used for WebMCP validation:
https://elastic-cloud-7bddb2h.shipstatic.com

## Run
`python -m http.server 8000`
then open `http://localhost:8000`

## Test
`node tests.mjs`
`node test-ui.mjs`
`node test-webmcp.mjs`

## Claim ceiling
EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY

Not a truth detector, scientific validator, medical/legal tool, or general automatic fact checker.
