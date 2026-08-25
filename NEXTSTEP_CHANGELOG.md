# NextStep Hacks 2026 — Before / During Disclosure

## Before the NextStep-specific build

The existing ProofPath baseline was already created and submitted before this Earth Forward extension was developed.

Baseline authority:
- repository: `lbkapcsolat-dotcom/ProofPath`
- branch: `main`
- commit: `537e276724a75b9f5f45404c550712b84f56d046`

Pre-existing components:
- generic claim/evidence input UI;
- three-class SUPPORTED / CONTRADICTED / INSUFFICIENT classifier;
- browser-side softmax/logistic-regression engine;
- generic labeled training examples and generic holdout examples;
- generic educational evidence-assessment claim ceiling.

## Developed during the NextStep hackathon period

The following work was developed on branch `nextstep-earth-evidence-v1` after the NextStep submission period opened:

- new Earth-specific 32-pair training corpus;
- new separate 10-pair Earth holdout/demo set;
- environmental category detection for Climate, Energy, Water, Waste, Biodiversity, Transport, and General;
- new `Next evidence needed` guidance that identifies the missing baseline, comparison, time window, scale, measurement, or independent replication step;
- Earth Forward user interface and environmental examples;
- new claim ceiling: `EDUCATIONAL_ENVIRONMENTAL_EVIDENCE_ASSESSMENT_ONLY`;
- Earth-specific benchmark tests and UI checks;
- documentation separating inherited ProofPath infrastructure from newly developed NextStep work.

## Cross-submission disclosure

The underlying ProofPath project has been submitted to other hackathons. This NextStep entry is not represented as wholly new from zero. The inherited baseline is disclosed above, and the Earth Evidence additions are isolated on a separate development branch.

## Claim limits

Earth Evidence is an educational prototype. It is not a climate model, scientific validator, policy recommendation engine, or general-purpose fact checker. Its fixed holdout is a bounded implementation benchmark and must not be interpreted as general-world accuracy.
