# Earth Evidence — NextStep Earth Forward Build

Earth Evidence is a NextStep-specific environmental extension of ProofPath.

It teaches a disciplined question: does a piece of evidence **support**, **contradict**, or remain **insufficient** for an environmental claim — and what evidence should be collected next?

## Provenance

This branch starts from the submitted ProofPath baseline:

- repository: `lbkapcsolat-dotcom/ProofPath`
- baseline branch: `main`
- baseline commit: `537e276724a75b9f5f45404c550712b84f56d046`
- NextStep development branch: `nextstep-earth-evidence-v1`
- original ProofPath existed before this NextStep-specific extension

The baseline ProofPath submissions remain untouched on `main`.

## New work developed for NextStep

1. Earth-specific labeled corpus: 32 training claim/evidence pairs.
2. Separate untouched Earth holdout/demo set: 10 pairs.
3. Environmental category routing: Climate, Energy, Water, Waste, Biodiversity, Transport, General.
4. New `Next evidence needed` output that converts the model verdict into a concrete evidence-gathering question.
5. Earth Forward UI and environmental claim ceiling.
6. New Earth-specific automated benchmark and static UI tests.
7. Explicit before/during disclosure in `NEXTSTEP_CHANGELOG.md`.

## Model

The project reuses ProofPath's transparent browser-side three-class softmax/logistic-regression engine and retrains it at startup on the Earth-specific corpus.

Feature families include lexical overlap, coverage, negation mismatch, numeric mismatch, antonym conflict, contradiction cues, uncertainty cues, overclaim cues, and evidence/claim length ratio.

No external AI API, paid model, account, cloud inference service, CDN, or model download is required.

## Test

```bash
node tests.mjs
node test-ui.mjs
```

The fixed Earth holdout is intentionally small and curated. A passing holdout test is a bounded implementation check, not evidence of real-world environmental or scientific accuracy.

## Claim ceiling

`EDUCATIONAL_ENVIRONMENTAL_EVIDENCE_ASSESSMENT_ONLY`

Earth Evidence is not a climate model, scientific validator, policy recommendation engine, or automatic fact-checking service. Model score distributions are not calibrated scientific confidence.
