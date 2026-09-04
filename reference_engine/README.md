# ALPHA FULL 6D Reference Engine V1

Deterministic, dependency-light Python reference implementation of the approved ALPHA FULL 6D machine contract.

## What is implemented

- `ALPHA_OBJECT_ENVELOPE_V1` construction and validation
- structural module input/output schemas
- fail-closed guard kernel with fixed precedence
- GAP engine
- research-contract engine
- six-dimensional fixed-point priority scoring
- fail-closed batch aggregation and deterministic JobKey
- orthogonal artifact state machine
- smallest-safe-effective next-best-action engine
- canonical module receipts
- 12 deterministic positive/negative canaries
- two-run byte-exact/SHA256 replay closure
- adversarial invariant matrix with 1,600 deterministic property/metamorphic cases
- fail-closed malformed-input regression coverage
- adversarial two-run byte/SHA replay closure

## Run tests

```bash
python -m pytest -q
```

## Run reference closure

```bash
python scripts/run_reference_closure.py --out build/closure
```

A passing closure requires both isolated runs to match all 12 canaries and produce byte-identical `outputs.json`, `receipts.json`, and `manifest.sha256`.

## Claim ceiling

`ENGINE_REFERENCE_PASS` means the local reference implementation and deterministic replay closure passed. It does **not** mean runtime admission, production readiness, pointer promotion, external authority, or permission to mutate external systems.

## Run adversarial closure

```bash
python scripts/run_adversarial_closure.py --out build/adversarial_closure
```

The adversarial gate covers six invariant families: `UNKNOWN != MISSING`, hard `HOLD > score`, authority fail-closed behavior, proof-safe state transitions, required-batch fail-closed behavior, and smallest-safe NBA selection. A passing closure requires all 1,600 generated cases to pass in both isolated runs and the canonical reports/manifests to be byte-identical with equal SHA256 digests.

`ADVERSARIAL_REFERENCE_PASS` extends the local reference claim only. It still does **not** imply runtime admission, production readiness, pointer promotion, external authority, or permission to mutate external systems.
