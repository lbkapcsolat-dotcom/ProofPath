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

## Run
`python -m http.server 8000`
then open `http://localhost:8000`

## Test
`node tests.mjs`

## Claim ceiling
EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY

Not a truth detector, scientific validator, medical/legal tool, or general automatic fact checker.
