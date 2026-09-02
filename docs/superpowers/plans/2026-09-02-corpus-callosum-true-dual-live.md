# Corpus Callosum True Dual-Live Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stored GPT-side comparison with a true live OpenAI provider run over the exact immutable c934… packet, enforce fail-closed CI semantics, and produce deterministic structured GPT↔Gemini adjudication with an independent artifact readback.

**Architecture:** Keep the existing immutable packet builder and dual-live claim ontology. Add a provider-isolated GPT live runner using `OPENAI_API_KEY`, harden Gemini/preflight exit semantics, update the workflow so HOLD cannot appear as green CI, and adjudicate only normalized canonical claim vectors.

**Tech Stack:** Node.js 22, GitHub Actions, OpenAI Responses API, Google Generative Language API, SHA-256, JSON receipts.

**Spec:** `docs/superpowers/specs/2026-09-02-corpus-callosum-true-dual-live-design.md`

## Global Constraints

- Exact packet SHA256: `c934b241c00f3a9cf15f56f9239f96471a0d721d8161865cbcaa6c8165493024`.
- GPT job sees only `OPENAI_API_KEY`; Gemini job sees only `GEMINI_API_KEY`.
- No secret values in source, logs, artifacts, receipts, PR prose, or chat.
- Any semantic HOLD/FAIL must be non-success at CI level.
- Zero corpus writes, zero authority mutation, zero pointer promotion, zero global bind, zero runtime admission, zero external actuation.
- Gemini secret custody remains HOLD until explicit key rotation/revocation proof exists.

---

### Task 1: RED tests for fail-closed provider receipts

**Files:**
- Create: `test-true-dual-live-failclosed.mjs`
- Test: `.github/workflows/corpus-callosum-gemini-readonly.yml`

**Interfaces:**
- Consumes: existing receipt status conventions and immutable packet builder.
- Produces: assertions that PASS is required for exit 0 and HOLD must fail the job.

- [ ] Write a failing test that imports a new helper `semanticExitCode(status)` and asserts `PASS_* => 0`, `HOLD_* => 2`, `FAIL_* => 1`.
- [ ] Commit test only.
- [ ] Run the branch workflow and confirm the new test fails because the helper does not exist.

### Task 2: GREEN fail-closed helper + preflight repair

**Files:**
- Create: `gate-status.mjs`
- Modify: `gemini-live-zero-spend-preflight.mjs`
- Modify: `gemini-live-same-packet-run.mjs`
- Modify: `.github/workflows/corpus-callosum-gemini-readonly.yml`

**Interfaces:**
- Produces: `semanticExitCode(status)` and `emitReceiptAndExit(receipt)`.

- [ ] Implement minimal helper.
- [ ] Change successful Gemini metadata discovery to `PASS_AUTH_MODEL_READY`.
- [ ] Make HOLD/FAIL receipts exit non-zero after printing receipt.
- [ ] Keep `set -o pipefail` in every receipt-producing step.
- [ ] Run workflow and verify RED test turns GREEN.

### Task 3: RED test for live OpenAI provider contract

**Files:**
- Create: `test-openai-live-dual-structured-contract.mjs`
- Create later in GREEN: `openai-live-dual-structured-claim-run.mjs`

**Interfaces:**
- Required receipt status: `PASS_GPT_LIVE_OPENAI_API_STRUCTURED_CLAIM_VECTOR`.
- Required provider: `OpenAI`.
- Required surface: `Responses API`.
- Required packet SHA: c934…
- Required ontology: `ALPHA_NSH_DUAL_LIVE_CLAIM_ONTOLOGY_V1`.

- [ ] Write failing contract test for receipt normalization and provider isolation metadata.
- [ ] Commit test only.
- [ ] Run workflow and confirm failure because live OpenAI runner/receipt is missing.

### Task 4: GREEN live GPT Responses API runner

**Files:**
- Create: `openai-live-dual-structured-claim-run.mjs`
- Modify: `.github/workflows/corpus-callosum-gemini-readonly.yml`

**Interfaces:**
- Consumes: `OPENAI_API_KEY`, `buildCorpusCallosumReadOnlyBind`, `buildDualLiveStructuredClaimPrompt`, `normalizeDualLiveClaimRun`.
- Produces: `openai-live-dual-structured-claim-receipt.json`.

- [ ] Rebuild exact bind and reject non-c934 packet.
- [ ] Call `POST https://api.openai.com/v1/responses` with Authorization bearer header.
- [ ] Require JSON output containing packetSha256 + canonical claims.
- [ ] Normalize against the existing ontology.
- [ ] Emit PASS receipt only after successful live response + normalization.
- [ ] Emit HOLD and non-zero on auth/model/http/JSON/contract errors.
- [ ] Add workflow step whose env contains only `OPENAI_API_KEY`.
- [ ] Run workflow and verify live GPT receipt PASS.

### Task 5: Gemini canonical dual-live receipt hardening

**Files:**
- Modify: `gemini-live-dual-structured-claim-run.mjs`
- Modify: `.github/workflows/corpus-callosum-gemini-readonly.yml`

**Interfaces:**
- Produces: `gemini-live-dual-structured-claim-receipt.json` with same ontology and packet.

- [ ] Enforce exact c934 packet.
- [ ] Require canonical ontology exactly once each.
- [ ] Make all HOLD/FAIL paths non-zero.
- [ ] Run workflow and verify Gemini live structured receipt PASS.

### Task 6: Replace static ChatGPT-session receipt with true provider receipt

**Files:**
- Modify: `compute-dual-live-structured-adjudication-receipt.mjs`
- Modify: `dual-live-structured-claim-contract.mjs`
- Stop using as authority: `gpt-live-chatgpt-session-structured-receipt.json`

**Interfaces:**
- Consumes: OpenAI live receipt + Gemini live receipt.
- Produces: deterministic dual-live adjudication receipt.

- [ ] Add verifier for `PASS_GPT_LIVE_OPENAI_API_STRUCTURED_CLAIM_VECTOR`.
- [ ] Reject ChatGPT-session/static receipt mode for true-dual-live gate.
- [ ] Require both live receipts packet-identical and ontology-identical.
- [ ] Preserve deterministic claim-level classifier.
- [ ] Run tests for direct contradiction, authority conflict, representation variance, provenance shift, uncertainty asymmetry.

### Task 7: Workflow dependency and artifact wiring

**Files:**
- Modify: `.github/workflows/corpus-callosum-gemini-readonly.yml`

**Interfaces:**
- GPT live step -> OpenAI receipt.
- Gemini live step -> Gemini receipt.
- Adjudicator -> dual-live receipt.

- [ ] Ensure adjudication only runs after both provider steps PASS.
- [ ] Keep artifact upload under `if: always()`.
- [ ] Include both provider receipts + adjudication receipt in artifact.
- [ ] Verify no step receives both provider secrets.

### Task 8: Second independent readback

**Files:**
- No source mutation required.

- [ ] Read workflow job conclusion.
- [ ] Read individual provider/adjudication step conclusions.
- [ ] Fetch artifact metadata and digest.
- [ ] Download artifact and inspect receipt statuses.
- [ ] Verify both packet SHA values equal c934… and classification is deterministic.
- [ ] Record claim ceiling: functional dual-live PASS or HOLD.
- [ ] Keep `SECURITY_SECRET_CUSTODY=HOLD_ROTATION_REQUIRED` until Gemini rotation is separately proven.
