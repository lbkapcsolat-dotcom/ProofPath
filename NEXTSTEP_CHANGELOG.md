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

## Event-window delta V2 — Evidence Context Coverage Panel

This update was added during the still-open NextStep submission window. It does not replace the original classifier and does not change the fixed 10-pair Earth holdout set.

Added in V2:
- deterministic `Evidence Context Coverage` analysis for six fields: baseline, comparison, time window, spatial scale, measured outcome, and source/provenance;
- per-field `PRESENT`, `MISSING`, or explicit `NOT_APPLICABLE` output;
- UI panel that renders the six context checks next to the existing verdict and `Next evidence needed` guidance;
- negative coverage test proving a context-poor evidence statement remains `MISSING` on baseline, comparison, time window, spatial scale, and source/provenance;
- guard test preventing a bare source/year citation from being misclassified as a measured outcome;
- positive and explicit-not-applicable tests;
- preservation of the existing 10/10 fixed Earth holdout result.

Interpretation boundary:
- `PRESENT` means the lightweight deterministic detector found a matching context cue in the supplied evidence text;
- `MISSING` means the cue was not detected, not that the underlying fact is false or absent in the real world;
- `NOT_APPLICABLE` is only emitted when the supplied evidence explicitly marks the field as not applicable.

## Cross-submission disclosure

The underlying ProofPath project has been submitted to other hackathons. This NextStep entry is not represented as wholly new from zero. The inherited baseline is disclosed above, and the Earth Evidence additions are isolated on a separate development branch.

## Claim limits

Earth Evidence is an educational prototype. It is not a climate model, scientific validator, policy recommendation engine, or general-purpose fact checker. Its fixed holdout is a bounded implementation benchmark and must not be interpreted as general-world accuracy.
