# Corpus Callosum True Dual-Live Design

## Goal

Promote the current c934b241c00f3a9cf15f56f9239f96471a0d721d8161865cbcaa6c8165493024 shared-packet comparison from one live Gemini run plus a stored GPT receipt to a true dual-live, provider-isolated, fail-closed GPT↔Gemini adjudication pipeline.

## Immutable packet contract

Both provider jobs MUST rebuild `corpus-callosum-current-authority-fixture.json` through `buildCorpusCallosumReadOnlyBind()` and MUST reject any packet SHA other than `c934b241c00f3a9cf15f56f9239f96471a0d721d8161865cbcaa6c8165493024`.

## Provider isolation

- GPT job receives only `OPENAI_API_KEY`.
- Gemini job receives only `GEMINI_API_KEY`.
- Neither job may receive the other provider's secret.
- Secret values never appear in source, receipts, artifacts, logs, PR prose, or chat.

## Execution

### GPT

Use the OpenAI Responses API over HTTPS with `OPENAI_API_KEY` in the Authorization header. Build the prompt with `buildDualLiveStructuredClaimPrompt('GPT', bind)`. Require JSON structured output matching the canonical claim ontology.

### Gemini

Keep authenticated `gemini-3.7-flash` execution but use the same canonical ontology and packet binding as GPT.

## Canonical claim ontology

The existing `ALPHA_NSH_DUAL_LIVE_CLAIM_ONTOLOGY_V1` remains the authority for claim IDs. Both providers must return exactly one claim for each ontology ID and no extras.

## Fail-closed semantics

- `PASS_*` is the only semantic success state.
- Any `HOLD_*` or `FAIL_*` receipt must cause a non-zero process exit after the receipt has been written to stdout/file.
- Workflow steps that pipe through `tee` must use `set -o pipefail`.
- Adjudication must not run as a success gate unless both provider receipts are `PASS_*` and packet-identical.
- Artifact upload may use `if: always()` so failure evidence is retained without converting semantic HOLD into job success.

## Preflight semantics

A successful authentication/model discovery preflight returns `PASS_AUTH_MODEL_READY`. A HOLD preflight blocks the corresponding live provider job.

## Adjudication

Use structured claim vectors, not conclusion-string equality. Material divergence is restricted to deterministic claim-level conflicts such as direct polarity contradiction, authority conflict, or metric conflict. Representation variance, provenance shift, scope shift, omission, or uncertainty asymmetry remain bounded/non-material unless the deterministic contract explicitly elevates them.

## Receipts

Each provider receipt must include:

- gate/status
- provider/model/surface
- packet SHA256
- claim schema + ontology
- liveInferenceExecuted=true
- normalized structured claim run
- zeroCorpusWrites=true
- authorityMutation=false
- pointerPromotion=false
- globalBind=false
- runtimeAdmission=false
- externalActuation=false

The final dual-live receipt must include both normalized provider runs, deterministic claim relations, overall classification, packet SHA, and the same non-actuation boundary.

## Second independent readback

After the workflow completes, independently read back:

1. workflow job conclusion,
2. relevant step conclusions,
3. uploaded artifact metadata + digest,
4. provider receipt statuses,
5. packet SHA equality,
6. adjudication classification.

No merge, runtime admission, authority promotion, or global bind is part of this gate.

## Security close

The previously exposed Gemini credential remains `HOLD_ROTATION_REQUIRED` until a new Free Tier Gemini key is created, rebound to the GitHub `GEMINI_API_KEY` secret, and the old key is revoked. True dual-live functional PASS does not by itself close secret-custody security.
