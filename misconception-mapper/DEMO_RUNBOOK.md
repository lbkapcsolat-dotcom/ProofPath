# Misconception Mapper V1 — <= 2 Minute Demo Runbook

Target: 90–110 seconds. Hard ceiling: 120 seconds.

## 0:00–0:15 — Problem
Students often get a wrong answer but generic tutoring jumps straight to the solution. Misconception Mapper asks a smaller question: what bounded misconception pattern may be visible in the submitted steps?

## 0:15–0:28 — Zero-spend architecture
Show the one-screen app. State: static browser app, deterministic local heuristic path, no paid API, no database, no required network call.

## 0:28–0:55 — Canonical attempt
Enter:
- Problem: `Solve 3x + 5 = 20.`
- Attempt: `3x = 25, x = 8.33`
- Concept: Algebra

Press **Analyze attempt**. Show `Sign handling error` and the single Socratic hint:
`If you want to undo the constant term, what inverse operation should you apply to both sides?`

Emphasize that the app does not reveal the final answer first.

## 0:55–1:15 — Retry
Enter `3x = 15, x = 5` and press **Check retry**.
Show: `Improved — the previous misconception pattern was not detected in this retry.`

## 1:15–1:30 — Fail-closed contrast
Briefly demonstrate an unsupported concept or ambiguous input returning `Need more context` / `Unsupported concept`, not fabricated certainty.

## 1:30–1:45 — Technical proof
Show test command and PASS summary. Mention bounded taxonomy, confidence ceilings, offline core, malformed-model fallback, and originality-boundary test.

## 1:45–1:55 — Claim ceiling
Close with the exact claim:
`A prototype educational tool that identifies bounded misconception patterns and provides Socratic hints to support retry-based learning.`

## Acceptance checklist
- video <= 120 seconds
- canonical diagnosis shown
- hint before full solution
- corrected retry shown as improved
- zero-spend/offline statement shown
- no efficacy or ability-diagnosis claim
