# Misconception Mapper V1 — Evidence Gate

## Zero-spend
- Runtime dependencies: none.
- Paid APIs: none.
- Required network calls: none.
- Database: none.
- Hosting required for core operation: none; static files can run locally.
- Optional model adapter: disabled by default; malformed/unavailable adapters fall back to deterministic ranking.

## Originality boundary
- New application code lives only under `misconception-mapper/`.
- The subtree imports no root ProofPath runtime module.
- Existing ProofPath `app.js`, `model.js`, and `tests.mjs` are not used by the new core logic.
- Tests enforce this boundary.

## Safety / claim ceiling
Allowed claim only:

> A prototype educational tool that identifies bounded misconception patterns and provides Socratic hints to support retry-based learning.

Not claimed: validated learning improvement, diagnostic assessment of ability, universal misconception detection, or teacher replacement.

## Canonical acceptance case
Problem: `Solve 3x + 5 = 20.`
Attempt: `3x = 25, x = 8.33`
Expected bounded pattern: `sign_handling`
Hint: asks which inverse operation should be applied to both sides; does not reveal `x = 5`.
Retry: `3x = 15, x = 5`
Expected retry state: `improved`.
