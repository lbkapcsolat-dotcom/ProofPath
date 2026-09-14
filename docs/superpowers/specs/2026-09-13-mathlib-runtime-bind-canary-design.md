# Mathlib Formal Equivalence → Authoritative Runtime Bind Canary Design

Date: 2026-09-13
Branch: `design/namespace-safe-eq64`
Status: ARCHITECTURE APPROVED IN CHAT, IMPLEMENTATION NOT STARTED

## 1. Purpose

Advance from the proven formal equivalence between the custom natural-number-indexed homology presentation and mathlib homology to one bounded executable runtime canary.

The gate must prove that the exact pinned Lean engine containing the formal bridge is the engine actually executed on a concrete non-trivial homology witness, that the custom and mathlib routes induce the same runtime homology-class partition, that a controlled negative route is detected, and that an identical replay yields byte-identical outputs and a byte-identical content-addressed receipt.

Approved architecture:

```text
PYTHON ORCHESTRATOR
  -> exact source/toolchain SHA verification
  -> pinned Lean oracle build
  -> Lean oracle execution
       -> custom homology route
       -> mathlib homology route
       -> canonical class-equality observables
  -> negative control
  -> identical replay
  -> byte/SHA equality
  -> deterministic receipt
  -> independent readback
```

## 2. Antecedent

Implementation MUST refuse a runtime-equivalence claim unless the branch lineage contains:

```text
PASS_MATHLIB_HOMOLOGICAL_COMPLEX_INTEROPERABILITY_AND_HOMOLOGY_BRIDGE_V1
```

The runtime canary does not replace that theorem. It checks that the executable path is bound to the same pinned formal implementation and behaves consistently on a concrete witness.

## 3. Scope and claim ceiling

In scope: isolated Lean runtime oracle; Python standard-library orchestrator; exact source/executable SHA binding; pinned Lean and mathlib revision verification; one non-trivial finite chain-complex witness; custom-vs-mathlib class-equality observable; negative control; identical replay; output/receipt equality; fresh dependency rehash; CI-only authoritative runtime bind.

Out of scope: production consumer wiring, auto-registration, global bind, pointer mutation/promotion, deployment, production readiness, unrelated semantic identity, empirical/physical claims, network calls, paid services.

Maximum success claim:

```text
PASS_MATHLIB_FORMAL_EQUIVALENCE__AUTHORITATIVE_RUNTIME_BIND_CANARY_V1
AUTHORITATIVE_RUNTIME_BIND_SCOPE = ISOLATED_CI_CANARY_ONLY
GENERAL_RUNTIME_ADMISSION        = FALSE
GLOBAL_BIND                      = FALSE
POINTER_PROMOTION                = FALSE
PRODUCTION_READINESS             = FALSE
```

The broad production/general `RUNTIME_BIND = FALSE` policy remains false. The canary uses a separate scoped authority field so CI success cannot be read as system-wide admission.

## 4. Runtime observable

A general homology object is a quotient without a universally useful canonical serialized representative. Therefore compare the invariant observable that matters: equality of homology classes over a frozen finite witness set.

For representatives `r_0,...,r_k`, each route emits:

```text
M[i][j] = true iff [r_i] = [r_j] in H_n
```

Required positive condition:

```text
CUSTOM_CLASS_EQUALITY_MATRIX == MATHLIB_CLASS_EQUALITY_MATRIX
```

Canonical JSON bytes are compared exactly.

## 5. Frozen non-trivial witness

Use `ZMod 4` at degree 1:

```text
C_n = ZMod 4 for all n
d_1 : C_2 -> C_1 = multiplication by 2
d_0 : C_1 -> C_0 = 0
d_n : C_{n+1} -> C_n = 0 for n >= 2
```

Thus:

```text
im(d_1) = {0,2}
ker(d_0) = ZMod 4
H_1      = ZMod 4 / {0,2}
```

Frozen representatives: `[0,1,2,3]`.

Expected equality matrix:

```text
[
  [true,  false, true,  false],
  [false, true,  false, true ],
  [true,  false, true,  false],
  [false, true,  false, true ]
]
```

This is non-trivial and exhaustive over all degree-1 representatives.

## 6. Lean authoritative oracle

Create an isolated executable module, e.g.:

```text
formal/namespace-safe-eq64/runtime/MathlibRuntimeOracle.lean
```

It MUST import the committed bridge modules and pinned mathlib package. Python MUST NOT reimplement homology.

Custom route: decide equality for all 16 ordered representative pairs using the custom `NatIndexedChainData` / `NatHomologous` or quotient presentation.

Mathlib route: build the corresponding `ChainComplex Ab Nat`, form the degree-1 standard short complex, and decide equality for the same 16 pairs through mathlib's explicit kernel/range quotient machinery. The mathlib route MUST NOT call the custom equality predicate.

Oracle stdout is exactly one JSON object with no nondeterministic metadata:

```json
{
  "schema": "MATHLIB_RUNTIME_ORACLE_V1",
  "witness": "ZMOD4_H1_BOUNDARY_TIMES_2",
  "degree": 1,
  "representatives": [0,1,2,3],
  "custom_class_equality": [[true,false,true,false],[false,true,false,true],[true,false,true,false],[false,true,false,true]],
  "mathlib_class_equality": [[true,false,true,false],[false,true,false,true],[true,false,true,false],[false,true,false,true]],
  "class_equal": true,
  "negative_control": false
}
```

Malformed JSON, missing/extra fields, unexpected stdout, or non-zero exit is fail-closed.

## 7. Exact engine identity

Hash:

```text
ORACLE_SOURCE_SHA256
BRIDGE_SOURCE_SHA256
NAT_HOMOLOGY_SOURCE_SHA256
LEAN_TOOLCHAIN_SHA256
LAKE_MANIFEST_SHA256
MATHLIB_REVISION
ORACLE_BINARY_SHA256
```

Canonical engine manifest:

```json
{
  "schema": "MATHLIB_RUNTIME_ENGINE_ID_V1",
  "git_head_sha": "...",
  "oracle_source_sha256": "...",
  "bridge_source_sha256": "...",
  "nat_homology_source_sha256": "...",
  "lean_toolchain_sha256": "...",
  "lake_manifest_sha256": "...",
  "mathlib_revision": "0df444a360eaa60ab8c11dca51a86af692955474",
  "oracle_binary_sha256": "..."
}
```

Define:

```text
ENGINE_SHA256 = SHA256(canonical_json(engine_manifest))
```

The resolved mathlib revision must equal the expected commit before execution.

## 8. Python orchestrator

Create e.g.:

```text
formal/namespace-safe-eq64/runtime/runtime_bind_canary.py
```

Use only the Python standard library. Responsibilities: resolve repository root; verify inputs; hash engine identity; verify mathlib pin; build Lean oracle through a fixed argument vector; hash executable; execute with `subprocess.run(..., shell=False)`; reject timeout/signal/non-zero exit/stderr-policy/schema drift; persist canonical positive output; run negative control; run identical positive replay; require positive output-byte equality; independently build two deterministic receipts; require receipt-byte equality; fresh-read and rehash every dependency.

Canonical receipts MUST NOT contain timestamp, random nonce, UUID, hostname, absolute temp path, environment-derived authority, or other nondeterministic data.

## 9. Positive canary

Mandatory assertions:

```text
CUSTOM_MATRIX_EXPECTED       = PASS
MATHLIB_MATRIX_EXPECTED      = PASS
CUSTOM_VS_MATHLIB_EQUAL      = PASS
CLASS_PARTITION_NONTRIVIAL   = PASS
CLASS_COUNT                  = 2
REPRESENTATIVE_COVERAGE      = 4_OF_4
PAIR_COVERAGE                = 16_OF_16
```

Reject all-equal, all-distinct, empty, or malformed matrices.

## 10. Negative control

Test-only `--negative-control` mode constructs a second mathlib-side witness with incoming degree-1 boundary `0` instead of multiplication by `2`, while the custom route remains on the frozen authoritative witness.

Expected:

```text
custom partition          = {{0,2},{1,3}}
mathlib negative partition = {{0},{1},{2},{3}}
class_equal               = false
EXPECTED_NEGATIVE_CONTROL_DETECTED = PASS
```

A negative-control `class_equal = true` is a hard failure. Negative output is never eligible for an authoritative positive receipt.

## 11. Replay

After positive run A and the negative control, execute identical positive run B without rebuilding or mutating the engine.

Require:

```text
RUN_A_ENGINE_SHA256 == RUN_B_ENGINE_SHA256
RUN_A_STDOUT_BYTES == RUN_B_STDOUT_BYTES
RUN_A_CANONICAL_JSON_BYTES == RUN_B_CANONICAL_JSON_BYTES
RECEIPT_A_BYTES == RECEIPT_B_BYTES
RECEIPT_A_SHA256 == RECEIPT_B_SHA256
```

## 12. Receipt

Minimum deterministic receipt:

```json
{
  "schema": "MATHLIB_FORMAL_RUNTIME_BIND_RECEIPT_V1",
  "formal_gate": "PASS_MATHLIB_HOMOLOGICAL_COMPLEX_INTEROPERABILITY_AND_HOMOLOGY_BRIDGE_V1",
  "authority_scope": "ISOLATED_CI_CANARY_ONLY",
  "git_head_sha": "...",
  "engine_sha256": "...",
  "oracle_binary_sha256": "...",
  "mathlib_revision": "0df444a360eaa60ab8c11dca51a86af692955474",
  "witness_sha256": "...",
  "positive_output_sha256": "...",
  "custom_vs_mathlib_class_equal": true,
  "negative_control_detected": true,
  "replay_output_equal": true,
  "receipt_replay_equal": true,
  "general_runtime_admission": false,
  "global_bind": false,
  "pointer_promotion": false,
  "production_readiness": false
}
```

Independent readback reparses the receipt, rejects schema drift, recomputes engine/source/binary/witness/output hashes, confirms all authority-ceiling booleans remain false, and compares persisted bytes and SHA.

## 13. TDD sequence

No implementation code before RED tests.

```text
RED 1: oracle contract missing -> expected failure
GREEN 1: frozen witness + custom route
RED 2: mathlib class matrix missing -> expected failure
GREEN 2: independent mathlib quotient route
RED 3: exact engine SHA fields + one-byte mutation rejection
GREEN 3: engine manifest/hash bind
RED 4: negative control must be detected
GREEN 4: test-only negative mode
RED 5: identical replay + receipt equality
GREEN 5: deterministic orchestration and receipt generation
```

No test may be weakened or removed to obtain GREEN.

## 14. CI gate

Add a dedicated workflow, e.g. `.github/workflows/mathlib-runtime-bind-canary.yml`, operating on exact PR head:

```text
1. checkout exact commit
2. verify Lean toolchain pin
3. verify pinned mathlib revision
4. run existing formal bridge harness
5. run proof-escape scanner
6. run runtime oracle unit tests
7. build oracle executable
8. materialize ENGINE_SHA256
9. positive run A
10. negative control
11. positive run B
12. compare A/B output bytes
13. independently build receipt A/B
14. compare receipt bytes + SHA
15. fresh dependency readback/rehash
16. assert authority-scope ceilings
```

The existing same-head RCCA provider gate must also be green on the exact resulting commit before PASS.

## 15. Fail-closed conditions

Any of these prevents PASS:

```text
formal antecedent missing
branch/head mismatch
mathlib revision mismatch
source or binary SHA mismatch
oracle build failure/timeout/non-zero exit
unexpected stderr
malformed JSON or schema drift
custom expected matrix mismatch
mathlib expected matrix mismatch
custom/mathlib matrix inequality
negative control not detected
positive replay inequality
receipt replay inequality
fresh dependency rehash mismatch
proof escape detected
same-head RCCA not green
authority ceiling unexpectedly true
```

No weighted score, partial success, prior run, or nearby commit can override a mandatory failure.

## 16. Concurrency discipline

Before every write:

```text
READ_CURRENT_BRANCH_HEAD
COMPARE_WITH_EXPECTED_PARENT
VERIFY_NO_RUNTIME_BIND_FILE_CONFLICT
```

Unrelated commits may be preserved. Conflicting changes require fresh reconciliation. Every PASS claim names the exact commit SHA and workflow run IDs.

## 17. Security and cost

```text
ZERO_SPEND         = TRUE
NETWORK_DURING_RUN = FALSE
SHELL_TRUE         = FORBIDDEN
SECRETS_REQUIRED   = FALSE
REMOTE_ACTUATION   = FALSE
PRODUCTION_WRITE   = FALSE
```

## 18. Success state

```text
PASS_MATHLIB_FORMAL_EQUIVALENCE__AUTHORITATIVE_RUNTIME_BIND_CANARY_V1

FORMAL_EQUIVALENCE            = PASS
EXACT_ENGINE_SHA              = PASS
CUSTOM_VS_MATHLIB_CLASS_EQUAL = PASS
NEGATIVE_CONTROL              = PASS
IDENTICAL_REPLAY              = PASS
RECEIPT_EQUALITY              = PASS
FRESH_READBACK                = PASS
RCCA_SAME_HEAD                = PASS

AUTHORITATIVE_RUNTIME_BIND_SCOPE = ISOLATED_CI_CANARY_ONLY
GENERAL_RUNTIME_ADMISSION        = FALSE
GLOBAL_BIND                      = FALSE
POINTER_PROMOTION                = FALSE
PRODUCTION_READINESS             = FALSE
```

A later runtime-consumer/admission gate requires separate authorization; it is not implied by this canary.
