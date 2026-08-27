# Misconception Mapper V1 — Design

Date: 2026-08-27
Target: Prometheus September AI Challenge 2
Status: DESIGN_FREEZE_CANDIDATE

## 1. Goal
Build a zero-spend educational AI tool that helps a student understand *why* an answer is wrong rather than immediately revealing the correct answer.

Primary flow:

STUDENT ANSWER → MISCONCEPTION CLASSIFIER → SOCRATIC HINT → RETRY → LEARNING STATE

The product should maximize educational impact, meaningful AI/ML use, technical execution, and clarity in a <=2 minute demo.

## 2. Competition constraints
- Participant must satisfy the official Devpost eligibility requirements.
- Core application logic must be new for the hackathon window.
- Solo participation is allowed.
- Demo video must be no longer than 2 minutes.
- Zero-spend: no paid APIs, paid credits, paid hosting, or purchase-dependent features.

## 3. Scope
### In scope
- One focused subject domain for V1: introductory algebra and physics misconceptions.
- Student enters a question/context and their attempted answer.
- System classifies likely misconception from a bounded taxonomy.
- System explains the diagnosis in plain language without exposing hidden reasoning.
- System gives one Socratic hint rather than the final answer.
- Student retries.
- System records whether the retry improved and shows a lightweight learning-state summary.
- Fully deterministic fallback when no AI/model inference is available.

### Out of scope
- General-purpose tutoring across every subject.
- High-stakes grading.
- Student profiling beyond the current local session.
- Cloud accounts, payments, analytics pipelines, or persistent personal data.
- Claims of clinical, psychological, or pedagogical diagnosis.

## 4. Product behavior
### Input
- Problem statement.
- Student's attempted answer.
- Optional expected concept tag chosen from the supported V1 domain.

### Misconception taxonomy
Initial bounded taxonomy:
1. Sign inversion / sign handling error.
2. Operation-order error.
3. Equality-as-action misunderstanding.
4. Variable isolation error.
5. Proportional reasoning error.
6. Equilibrium vs. stability confusion.
7. Velocity vs. acceleration confusion.
8. Correlation-style pattern match / insufficient evidence.
9. Unknown / insufficient context.

Each class has:
- id
- short label
- detection signals
- confidence ceiling
- safe Socratic hint template
- retry check

### Output
- `Likely misconception` with calibrated confidence wording.
- `Why this may be happening` in one concise sentence.
- `Try this next` with exactly one hint/question.
- Retry box.
- Updated state: `improved`, `same pattern`, or `uncertain`.

## 5. AI / ML strategy
V1 uses a hybrid design so the project remains zero-spend and fail-closed:

1. **Local heuristic layer**
   - Deterministic pattern features from the submitted answer.
   - Produces a ranked set of candidate misconception classes.

2. **Optional local/client-side model layer**
   - Only if a genuinely zero-cost browser/local model can be bundled or loaded without metered calls.
   - Model may rerank candidate classes or generate a bounded paraphrase of an approved hint.
   - Model must never be required for the core demo path.

3. **Guardrail layer**
   - No fabricated certainty.
   - If confidence is low: return `uncertain / need more context`.
   - Never claim to infer ability, intelligence, disability, or mental state.
   - No hidden chain-of-thought exposure.

This architecture makes AI meaningful while preserving zero-spend and deterministic testability.

## 6. Architecture
### Frontend
Single-page web app.

Components:
- `ProblemInput`
- `AttemptInput`
- `ConceptSelector`
- `DiagnosisCard`
- `HintCard`
- `RetryPanel`
- `LearningStatePanel`

### Core engine
Pure functions where possible:
- `extractFeatures(problem, attempt, concept)`
- `rankMisconceptions(features)`
- `selectDiagnosis(candidates)`
- `buildHint(diagnosis, context)`
- `evaluateRetry(previous, retry)`

### Data
Local-only session state:
- current problem
- current attempt
- diagnosis
- hint
- retry
- retry outcome

No remote database required for V1.

## 7. Error handling / fail-closed rules
- Empty attempt → no diagnosis; ask for an attempt.
- Unsupported concept → bounded `unsupported` response.
- Multiple close classes → `uncertain` and ask one clarifying question.
- Optional model unavailable → deterministic heuristic output still works.
- Any malformed model output → discard and use approved local template.
- No network dependency may block the core flow.

## 8. UX principles
- One-screen primary workflow.
- Student sees the hint before any full solution.
- Minimal text; strongest visual emphasis on `Likely misconception` and `Try this next`.
- No red punitive grading language.
- Retry is the central action.
- Demo must show a complete transformation in under 30 seconds of screen time.

## 9. Demo scenario
Recommended demo case:

Problem: `Solve 3x + 5 = 20.`
Student attempt: `3x = 25, x = 8.33`
Diagnosis: likely sign/operation reversal around moving `+5` across equality.
Hint: `If you want to undo +5, what operation should you apply to both sides?`
Retry: `3x = 15, x = 5`
Outcome: `Improved — previous misconception not detected in retry.`

Second optional 10-second contrast:
Physics prompt showing equilibrium-vs-stability confusion.

## 10. Testing strategy
### Unit tests
- Feature extraction for each misconception class.
- Ranking tie behavior.
- Confidence ceilings.
- Hint-template selection.
- Retry classification.
- Unknown/unsupported inputs.

### Negative tests
- Empty input.
- Ambiguous answer.
- Prompt-injection text inside student answer.
- Model layer disabled/offline.
- Malformed optional model output.
- Unsupported domain.

### Demo acceptance test
Given the canonical algebra case:
1. app loads without paid/external dependency,
2. attempt is accepted,
3. correct misconception class is surfaced,
4. final answer is not revealed before retry,
5. hint is shown,
6. corrected retry is recognized as improved.

## 11. Zero-spend policy
HARD REQUIREMENTS:
- No paid API.
- No metered browser automation in the product.
- No credit-consuming inference provider.
- No required paid deployment.
- No purchase, trial conversion, card authorization, or billing setup.

If a proposed model or host cannot be proven zero-cost for the required use, it is excluded from V1.

## 12. Originality boundary
- New Misconception Mapper core modules are written fresh on this branch during the hackathon window.
- Existing ProofPath code is not copied into the core application logic.
- Existing general tooling may be used only as build/test infrastructure where allowed by the competition rules.
- The project must stand alone as an educational misconception-diagnosis tutor, not as a renamed ProofPath submission.

## 13. Success criteria
PASS_BUILD only if:
- all core tests pass,
- canonical demo case passes end-to-end,
- zero paid dependencies,
- no required network dependency for core flow,
- no unsupported high-stakes claims,
- new core logic is isolated from existing ProofPath implementation,
- <=2 minute demo can clearly show problem → diagnosis → hint → retry → improvement.

## 14. Claim ceiling
Allowed claim:
`A prototype educational tool that identifies bounded misconception patterns and provides Socratic hints to support retry-based learning.`

Not allowed:
- proven learning improvement,
- diagnostic assessment of student ability,
- universal misconception detection,
- teacher replacement,
- validated educational efficacy without evidence.

## 15. Next gate
DESIGN REVIEW → IMPLEMENTATION PLAN → TDD BUILD → ZERO-SPEND CANARY → END-TO-END DEMO → 2-MIN VIDEO → DEVPOST SUBMISSION → FRESH READBACK
