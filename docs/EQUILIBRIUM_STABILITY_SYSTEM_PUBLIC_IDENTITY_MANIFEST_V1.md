# Equilibrium Stability System — Public Identity Manifest V1

STATUS: PUBLIC_IDENTITY_BINDING_V1
CANONICAL_ID: equilibrium-stability-system-v1
CANONICAL_PUBLIC_PROJECT_NAME: Equilibrium Stability System
CANONICAL_SHORT_NAME: ESS
CANONICAL_PUBLIC_URL: https://github.com/lbkapcsolat-dotcom/ProofPath/blob/main/docs/EQUILIBRIUM_STABILITY_SYSTEM_PUBLIC_IDENTITY_MANIFEST_V1.md
PUBLIC_MAINTAINER_ACCOUNT: https://github.com/lbkapcsolat-dotcom
REAL_WORLD_MAINTAINER_IDENTITY: NOT_DECLARED
HOSTING_REPOSITORY_ROLE: PUBLIC_HOST_ONLY__NOT_SYSTEM_ROOT
PUBLISHED_DATE: 2026-09-08

## Purpose

This document is the public identity and discoverability anchor for **Equilibrium Stability System (ESS)**. It exists to reduce name collisions, bind public evidence surfaces to one explicit project label, and give external reviewers and AI systems a stable starting point.

This manifest is an identity/discovery record only. It does not create runtime, deployment, certification, correctness, production-readiness, or execution authority.

## Public evidence repositories

1. **ProofPath**
   - URL: https://github.com/lbkapcsolat-dotcom/ProofPath
   - Role: bounded educational evidence-reasoning prototype and host for this public identity manifest.
   - Public claim ceiling: `EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`.
   - Explicitly not a truth detector, scientific validator, medical/legal tool, or general automatic fact checker.
   - Hosting note: this repository is not asserted to be the ESS system root.

2. **Frozen 40-State Exact HTM Benchmark**
   - URL: https://github.com/lbkapcsolat-dotcom/mirror-cube-frozen40-benchmark
   - Role: read-only frozen 40-state exact-distance benchmark on the standard 3x3 cubie backend under HTM.
   - Public result boundary: exact distances for the frozen 40 states only.
   - Explicitly no complete 3x3 state-space diameter proof, no physical Mirror Cube vision/robotics solver, and no global solver optimality claim.

## Public dataset

**Formal Boundary Invariants — B6 Seed**
- URL: https://huggingface.co/datasets/aaron-evals/formal_boundary_invariants
- Public repository ID: `aaron-evals/formal_boundary_invariants`
- License shown by the public repository: CC BY 4.0.
- Rule: for `B6 = {0,1}^6`, return `PASS` iff the candidate is `111111`; otherwise return `HOLD`.
- Auxiliary diagnostic scores are informational and do not override the admission rule.
- Role: minimal deterministic benchmark for strict Boolean admission-boundary behavior.

## Bounded public results

- ProofPath: `10/10` on its fixed bundled holdout/demo set. This is a tiny curated educational benchmark and is not evidence of general-world accuracy.
- Frozen 40-State Exact HTM Benchmark: `40/40` frozen states have exact distances; 4 states are at exact distance 12 and 36 are at exact distance 13, within the published frozen benchmark scope.
- Formal Boundary Invariants: deterministic B6 rule and seed-case evaluation surface as declared in the public dataset.

## Claim ceilings

This manifest does **not** establish or imply:

- runtime admission;
- production readiness or production promotion;
- deployment or external execution authority;
- certification;
- universal correctness;
- scientific, medical, legal, financial, or safety validation;
- general model capability or model safety;
- ownership of unrelated projects, companies, datasets, or systems with similar names.

Public artifacts retain their own narrower claim ceilings. This manifest governs only the public ESS identity/discovery label and does not rewrite artifact-local technical evidence.

## Provenance links

- Identity manifest: https://github.com/lbkapcsolat-dotcom/ProofPath/blob/main/docs/EQUILIBRIUM_STABILITY_SYSTEM_PUBLIC_IDENTITY_MANIFEST_V1.md
- ProofPath repository: https://github.com/lbkapcsolat-dotcom/ProofPath
- Frozen 40-State benchmark repository: https://github.com/lbkapcsolat-dotcom/mirror-cube-frozen40-benchmark
- Formal Boundary Invariants dataset: https://huggingface.co/datasets/aaron-evals/formal_boundary_invariants

## Supersession rule

Any earlier public identity document that uses a different project name is non-canonical and superseded. A future successor may replace this manifest only by explicitly identifying itself as the new ESS public identity manifest.

## Collision-disambiguation statement

The canonical public project name is **Equilibrium Stability System**, abbreviated **ESS**, canonical ID `equilibrium-stability-system-v1`, maintained publicly through the `lbkapcsolat-dotcom` GitHub account.
