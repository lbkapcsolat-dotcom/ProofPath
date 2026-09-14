# Mathlib Formal Equivalence → Authoritative Runtime Bind Canary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one isolated CI-only runtime canary that proves the executed pinned Lean engine agrees between the custom and mathlib degree-1 homology-class equality routes on a frozen non-trivial witness, detects a controlled negative route, reproduces byte-identically, and emits a content-addressed receipt with fresh dependency readback.

**Architecture:** A Python standard-library orchestrator verifies exact source/toolchain/mathlib identity, builds and invokes a pinned Lean executable with `shell=False`, validates the oracle's canonical JSON, executes positive A → negative → positive B, and requires exact output/receipt equality. The Lean executable owns both homology computations; Python never reimplements homology. Runtime authority is bounded to the isolated CI canary and does not imply general runtime admission, global bind, pointer promotion, or production readiness.

**Tech Stack:** Lean 4.33.1, pinned mathlib `0df444a360eaa60ab8c11dca51a86af692955474`, Lake, `ZMod 4`, Python 3 standard library (`argparse`, `hashlib`, `json`, `pathlib`, `subprocess`, `tempfile`, `unittest`), SHA256, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-13-mathlib-runtime-bind-canary-design.md`

## Global Constraints

- Antecedent formal gate: `PASS_MATHLIB_HOMOLOGICAL_COMPLEX_INTEROPERABILITY_AND_HOMOLOGY_BRIDGE_V1`.
- Expected mathlib revision: `0df444a360eaa60ab8c11dca51a86af692955474`.
- Frozen witness: `ZMOD4_H1_BOUNDARY_TIMES_2` at degree `1` with representatives `[0,1,2,3]`.
- Expected positive equality matrix: `[[true,false,true,false],[false,true,false,true],[true,false,true,false],[false,true,false,true]]`.
- Negative control changes only the mathlib-side incoming degree-1 boundary from multiplication by `2` to `0`; it MUST be detected as unequal.
- Python MUST NOT compute homology or derive the expected matrix from an independent Python implementation.
- All subprocess calls use a fixed argv list and `shell=False`.
- Oracle stdout is exactly one UTF-8 JSON object plus one trailing newline; unexpected stderr is failure.
- Receipt inputs contain no timestamp, nonce, UUID, hostname, absolute temp path, randomness, or environment-derived authority.
- `AUTHORITATIVE_RUNTIME_BIND_SCOPE = ISOLATED_CI_CANARY_ONLY` is the maximum positive runtime claim.
- `GENERAL_RUNTIME_ADMISSION = FALSE`.
- `GLOBAL_BIND = FALSE`.
- `POINTER_PROMOTION = FALSE`.
- `PRODUCTION_READINESS = FALSE`.
- `ZERO_SPEND = TRUE`.
- `NETWORK_DURING_RUN = FALSE` after dependencies are available.
- `SECRETS_REQUIRED = FALSE`.
- PR #20 remains draft and unmerged throughout this gate.
- Before every branch write: read current branch head, compare against the expected parent, and preserve unrelated concurrent commits; never force-update the branch.

---

## File Structure

Create or modify only the following runtime-bind surfaces unless a compile error demonstrates that one additional narrowly-scoped import/config edit is required:

```text
formal/namespace-safe-eq64/
├── lakefile.lean                                  # modify: add isolated oracle executable target
├── RuntimeBindOracle.lean                         # create: frozen witness + custom/mathlib class matrices + JSON CLI
├── runtime/
│   ├── __init__.py                                # create: empty package marker
│   ├── runtime_bind_canary.py                     # create: exact-SHA orchestrator + receipt/readback
│   └── test_runtime_bind_canary.py                # create: Python TDD contract/negative/replay tests
└── RuntimeBindOracleTest.lean                     # create: Lean-level RED/GREEN contract checks
.github/workflows/
└── mathlib-runtime-bind-canary.yml                # create: exact-head CI gate
```

Do not alter `MathlibHomologicalComplexBridge.lean`, `NatIndexedHomologyGate.lean`, or the existing formal theorem statements merely to make the runtime gate pass. If the runtime implementation reveals a missing public theorem/interface, stop and open a new formal prerequisite gate rather than weakening the bridge.

---

### Task 1: Freeze the Lean oracle interface with a real RED gate

**Files:**
- Create: `formal/namespace-safe-eq64/RuntimeBindOracleTest.lean`
- Modify later in this task only after RED is observed: `formal/namespace-safe-eq64/RuntimeBindOracle.lean`

**Interfaces:**
- Consumes: `HomologyGate.NatIndexedChainData`, `HomologyGate.mathlibChainComplex`, `HomologyGate.mathlibDegreeHomologyMap_eq_iff` from the existing formal package.
- Produces: `RuntimeBindOracle.expectedMatrix`, `RuntimeBindOracle.customClassEq`, `RuntimeBindOracle.mathlibClassEq`, `RuntimeBindOracle.positiveResult`, `RuntimeBindOracle.negativeResult`.

- [ ] **Step 1: Write the failing Lean contract test before the oracle exists**

Create `RuntimeBindOracleTest.lean` with the exact checks:

```lean
import RuntimeBindOracle

open RuntimeBindOracle

#check expectedMatrix
#check customClassEq
#check mathlibClassEq
#check positiveResult
#check negativeResult
#check positive_custom_matches_expected
#check positive_mathlib_matches_expected
#check positive_routes_equal
#check negative_routes_differ
```

- [ ] **Step 2: Run the theorem harness and record RED**

Run from `formal/namespace-safe-eq64`:

```bash
lake env lean RuntimeBindOracleTest.lean
```

Expected: non-zero exit because `RuntimeBindOracle` and/or the listed symbols do not exist. Record the exact first unknown identifier/module error in the implementation log. A syntax/import error unrelated to the missing oracle is not an acceptable RED and must be corrected before proceeding.

- [ ] **Step 3: Add only the executable target declaration required for the later oracle build**

Modify `lakefile.lean` by preserving the existing package/library declarations and adding:

```lean
lean_exe runtimeBindOracle where
  root := `RuntimeBindOracle
```

Do not remove or rename the current default library target.

- [ ] **Step 4: Re-run RED after the Lake target exists**

```bash
lake env lean RuntimeBindOracleTest.lean
```

Expected: still non-zero for missing runtime-oracle symbols, proving target configuration alone cannot make the contract green.

- [ ] **Step 5: Commit only the RED contract and executable-target configuration**

```bash
git add formal/namespace-safe-eq64/RuntimeBindOracleTest.lean formal/namespace-safe-eq64/lakefile.lean
git commit -m "test(formal): add RED mathlib runtime bind oracle contract"
```

CI on this commit is expected to fail the new runtime contract; existing unrelated gates must not be weakened to mask that failure.

---

### Task 2: Implement the frozen `ZMod 4` witness and custom class-equality route

**Files:**
- Create: `formal/namespace-safe-eq64/RuntimeBindOracle.lean`
- Test: `formal/namespace-safe-eq64/RuntimeBindOracleTest.lean`

**Interfaces:**
- Consumes: existing `NatIndexedChainData` and `NatHomologous` definitions.
- Produces:
  - `abbrev Z4 := ZMod 4`
  - `def witnessChain : NatIndexedChainData (fun _ => Z4)`
  - `def representatives : List Z4`
  - `def expectedMatrix : List (List Bool)`
  - `def customClassEq (a b : Z4) : Bool`
  - `def customMatrix : List (List Bool)`
  - theorem `positive_custom_matches_expected : customMatrix = expectedMatrix`.

- [ ] **Step 1: Add the minimal frozen witness**

Use degree-dependent boundaries equivalent to:

```lean
abbrev Z4 := ZMod 4

def z4Boundary (n : Nat) : Z4 →+ Z4 :=
  match n with
  | 1 => 2 • AddMonoidHom.id Z4
  | _ => 0

def witnessChain : NatIndexedChainData (fun _ : Nat => Z4) where
  boundary := z4Boundary
  boundary_sq := by
    intro n x
    cases n <;> simp [z4Boundary]
```

If `2 • AddMonoidHom.id Z4` does not elaborate under the pinned mathlib API, use `AddMonoidHom.mk' (fun x => 2 * x) (by intro x y; ring)` or the smallest equivalent bundled-hom definition accepted by Lean. Do not change the mathematical witness.

- [ ] **Step 2: Define the frozen representatives and literal expected matrix**

```lean
def representatives : List Z4 := [0, 1, 2, 3]

def expectedMatrix : List (List Bool) :=
  [ [true,  false, true,  false]
  , [false, true,  false, true ]
  , [true,  false, true,  false]
  , [false, true,  false, true ]
  ]
```

The expected matrix is deliberately literal so the implementation cannot manufacture its own oracle expectation.

- [ ] **Step 3: Define custom class equality from the custom homology relation**

For degree 1, decide `NatHomologous witnessChain 1` for cycle representatives whose outgoing differential is zero. The implementation must use the custom relation or quotient API, not the mathlib route. Prefer:

```lean
def degreeOneCycle (x : Z4) : NatCycle witnessChain 1 :=
  ⟨x, by simp [NatInKernel, natDegreeBoundary, witnessChain, z4Boundary]⟩

def customClassEq (a b : Z4) : Bool :=
  decide (NatHomologous witnessChain 1 (degreeOneCycle a) (degreeOneCycle b))
```

If decidability is not synthesized directly for the existential relation, prove the equivalent finite predicate `b = a ∨ b = a + 2` inside Lean and use that proof to derive a `Decidable` result. The proof must remain custom-side and must not call `mathlibClassEq`.

- [ ] **Step 4: Build `customMatrix` from all 16 ordered pairs**

```lean
def customMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => customClassEq a b
```

- [ ] **Step 5: Prove the custom route equals the literal expected matrix**

```lean
theorem positive_custom_matches_expected : customMatrix = expectedMatrix := by
  native_decide
```

If `native_decide` is unavailable for the involved quotient/relation term, reduce the finite witness to the proved finite predicate and use `decide`/`norm_num` without `axiom`, `sorry`, `admit`, or `unsafe` proof escapes.

- [ ] **Step 6: Run the Lean test and confirm the custom half is GREEN while mathlib symbols remain RED**

```bash
lake env lean RuntimeBindOracleTest.lean
```

Expected: `expectedMatrix`, `customClassEq`, and `positive_custom_matches_expected` resolve; missing `mathlibClassEq`/final result symbols still fail. This is intentional staged GREEN/RED.

- [ ] **Step 7: Commit the custom route**

```bash
git add formal/namespace-safe-eq64/RuntimeBindOracle.lean
git commit -m "feat(formal): add frozen ZMod4 custom homology runtime witness"
```

---

### Task 3: Add an independent mathlib class-equality route and complete the positive oracle

**Files:**
- Modify: `formal/namespace-safe-eq64/RuntimeBindOracle.lean`
- Test: `formal/namespace-safe-eq64/RuntimeBindOracleTest.lean`

**Interfaces:**
- Consumes: `witnessChain`, existing `mathlibChainComplex`, and mathlib explicit short-complex kernel/range quotient API.
- Produces:
  - `def mathlibClassEq (a b : Z4) : Bool`
  - `def mathlibMatrix : List (List Bool)`
  - theorem `positive_mathlib_matches_expected`
  - theorem `positive_routes_equal`.

- [ ] **Step 1: Construct the standard degree-1 mathlib short complex from `mathlibChainComplex witnessChain`**

Use exactly the already-proved bridge carrier/differential, with the short complex at indices `2 → 1 → 0`:

```lean
private abbrev standardShort : ShortComplex Ab :=
  (mathlibChainComplex witnessChain).sc' 2 1 0
```

- [ ] **Step 2: Build mathlib kernel-cycle representatives independently**

For each `x : Z4`, construct an element of `AddMonoidHom.ker standardShort.g.hom`; the proof of kernel membership uses the mathlib differential theorem, not `customClassEq`.

```lean
private def mathlibCycle (x : Z4) : AddMonoidHom.ker standardShort.g.hom := by
  refine ⟨x, ?_⟩
  change (ConcreteCategory.hom ((mathlibChainComplex witnessChain).d 1 0)) x = 0
  simp [mathlib_chain_d_succ_apply, witnessChain, z4Boundary]
```

- [ ] **Step 3: Decide equality in mathlib's explicit quotient**

Define the quotient:

```lean
private abbrev StandardH1 :=
  (AddMonoidHom.ker standardShort.g.hom) ⧸ AddMonoidHom.range standardShort.abToCycles
```

Map with `QuotientAddGroup.mk'` and decide equality of the resulting finite quotient values. The route may use `ShortComplex.abToCycles` and `QuotientAddGroup.mk'_eq_mk'`; it MUST NOT call `NatHomologous`, `customClassEq`, or `customMatrix`.

- [ ] **Step 4: Define the mathlib matrix and prove the literal expected matrix**

```lean
def mathlibMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => mathlibClassEq a b

theorem positive_mathlib_matches_expected : mathlibMatrix = expectedMatrix := by
  native_decide

theorem positive_routes_equal : customMatrix = mathlibMatrix := by
  rw [positive_custom_matches_expected, positive_mathlib_matches_expected]
```

- [ ] **Step 5: Run the full Lean oracle contract**

```bash
lake env lean RuntimeBindOracleTest.lean
```

Expected: remaining failure only for negative/result/CLI symbols not yet implemented. If custom and mathlib matrices disagree, STOP and diagnose the first pair; do not normalize the expected matrix to match the implementation.

- [ ] **Step 6: Commit the independent mathlib route**

```bash
git add formal/namespace-safe-eq64/RuntimeBindOracle.lean
git commit -m "feat(formal): add independent mathlib H1 runtime equality route"
```

---

### Task 4: Add the controlled negative oracle and deterministic JSON executable contract

**Files:**
- Modify: `formal/namespace-safe-eq64/RuntimeBindOracle.lean`
- Test: `formal/namespace-safe-eq64/RuntimeBindOracleTest.lean`

**Interfaces:**
- Produces:
  - `def positiveResult : String`
  - `def negativeResult : String`
  - theorem/decidable check `negative_routes_differ`
  - CLI modes: no args = positive; `--negative-control` = negative; any other argv = exit non-zero.

- [ ] **Step 1: Implement a mathlib-only negative witness**

Create a second mathlib chain complex with the same carriers but zero incoming degree-1 boundary. The custom route remains `witnessChain`. The negative mathlib degree-1 partition must therefore be all singletons over `[0,1,2,3]`.

Literal expected negative matrix:

```lean
def expectedNegativeMathlibMatrix : List (List Bool) :=
  [ [true,  false, false, false]
  , [false, true,  false, false]
  , [false, false, true,  false]
  , [false, false, false, true ]
  ]
```

Prove the negative mathlib matrix equals this literal matrix and prove it differs from `customMatrix`.

- [ ] **Step 2: Define a tiny deterministic JSON renderer inside Lean**

Do not depend on object-key iteration order. Render fields in this exact order:

```text
schema
witness
degree
representatives
custom_class_equality
mathlib_class_equality
class_equal
negative_control
```

Positive values:

```text
schema = MATHLIB_RUNTIME_ORACLE_V1
witness = ZMOD4_H1_BOUNDARY_TIMES_2
degree = 1
representatives = [0,1,2,3]
class_equal = true
negative_control = false
```

Negative values keep the same custom matrix, emit the singleton mathlib matrix, and set:

```text
class_equal = false
negative_control = true
```

- [ ] **Step 3: Implement CLI argument handling**

Use `IO.getArgs`. Accepted argv sets are exactly:

```text
[]
["--negative-control"]
```

Any other argv writes a short error to stderr and exits with a non-zero code. Positive and negative success paths write exactly one JSON line to stdout and nothing to stderr.

- [ ] **Step 4: Complete the Lean contract checks**

Make all checks in `RuntimeBindOracleTest.lean` resolve, including:

```lean
#check positiveResult
#check negativeResult
#check negative_routes_differ
```

- [ ] **Step 5: Run Lean unit/harness checks and build the executable**

```bash
lake env lean RuntimeBindOracleTest.lean
lake build runtimeBindOracle
```

Expected: both exit 0.

- [ ] **Step 6: Execute the oracle directly in both modes**

```bash
.lake/build/bin/runtimeBindOracle
.lake/build/bin/runtimeBindOracle --negative-control
```

Expected: positive emits `class_equal:true,negative_control:false`; negative emits `class_equal:false,negative_control:true`. Save raw stdout bytes for inspection; there must be no stderr.

- [ ] **Step 7: Commit the completed Lean oracle**

```bash
git add formal/namespace-safe-eq64/RuntimeBindOracle.lean formal/namespace-safe-eq64/RuntimeBindOracleTest.lean
git commit -m "feat(formal): complete deterministic Lean runtime bind oracle"
```

---

### Task 5: RED-test exact engine identity and Python oracle validation

**Files:**
- Create: `formal/namespace-safe-eq64/runtime/__init__.py`
- Create: `formal/namespace-safe-eq64/runtime/test_runtime_bind_canary.py`
- Create later after RED: `formal/namespace-safe-eq64/runtime/runtime_bind_canary.py`

**Interfaces:**
- Planned Python public functions:

```python
canonical_json_bytes(value: object) -> bytes
sha256_bytes(data: bytes) -> str
read_mathlib_revision(root: Path) -> str
build_engine_manifest(root: Path, git_head_sha: str, oracle_binary: Path) -> dict
validate_oracle_output(raw: bytes, *, negative_control: bool) -> dict
run_oracle(binary: Path, *, negative_control: bool) -> bytes
build_receipt(...) -> dict
verify_receipt_dependencies(...) -> dict
run_canary(root: Path, git_head_sha: str, output_dir: Path) -> dict
```

- [ ] **Step 1: Write Python tests for canonical output and schema rejection before implementation exists**

Include tests equivalent to:

```python
class RuntimeBindCanaryTests(unittest.TestCase):
    def test_positive_oracle_contract_accepts_exact_matrix(self):
        raw = b'{"schema":"MATHLIB_RUNTIME_ORACLE_V1","witness":"ZMOD4_H1_BOUNDARY_TIMES_2","degree":1,"representatives":[0,1,2,3],"custom_class_equality":[[true,false,true,false],[false,true,false,true],[true,false,true,false],[false,true,false,true]],"mathlib_class_equality":[[true,false,true,false],[false,true,false,true],[true,false,true,false],[false,true,false,true]],"class_equal":true,"negative_control":false}\n'
        value = validate_oracle_output(raw, negative_control=False)
        self.assertTrue(value["class_equal"])

    def test_oracle_contract_rejects_extra_field(self):
        value = json.loads(EXACT_POSITIVE_JSON)
        value["extra"] = 1
        with self.assertRaisesRegex(ValueError, "ORACLE_FIELDS_MISMATCH"):
            validate_oracle_output(canonical_json_bytes(value) + b"\n", negative_control=False)
```

Also test: wrong schema, wrong witness, wrong representative order, malformed 4×4 matrix, all-equal matrix, all-distinct matrix, wrong expected positive matrix, positive marked negative, negative marked positive, extra stdout, invalid UTF-8, and missing trailing newline.

- [ ] **Step 2: Write engine-manifest mutation tests**

Use temporary files and assert that changing one byte of each dependency changes the computed engine SHA or triggers dependency mismatch. Cover at least:

```text
RuntimeBindOracle.lean
MathlibHomologicalComplexBridge.lean
NatIndexedHomologyGate.lean
lean-toolchain
lake-manifest.json
oracle binary
```

- [ ] **Step 3: Run Python tests and confirm RED**

```bash
python -m unittest formal.namespace-safe-eq64.runtime.test_runtime_bind_canary -v
```

Because the directory name contains a hyphen, the actual stable command must use discovery from repository root:

```bash
python -m unittest discover -s formal/namespace-safe-eq64/runtime -p 'test_runtime_bind_canary.py' -v
```

Expected: import/module failure because `runtime_bind_canary.py` is absent. The discovery form is the canonical command for all later tasks.

- [ ] **Step 4: Commit the RED Python tests only**

```bash
git add formal/namespace-safe-eq64/runtime/__init__.py formal/namespace-safe-eq64/runtime/test_runtime_bind_canary.py
git commit -m "test(formal): add RED authoritative runtime bind orchestrator tests"
```

---

### Task 6: Implement exact engine SHA, pin verification, and fail-closed oracle execution

**Files:**
- Create: `formal/namespace-safe-eq64/runtime/runtime_bind_canary.py`
- Test: `formal/namespace-safe-eq64/runtime/test_runtime_bind_canary.py`

**Interfaces:**
- Consumes: built oracle binary and committed formal/runtime source files.
- Produces: canonical engine manifest and validated positive/negative raw outputs.

- [ ] **Step 1: Implement canonical JSON and SHA helpers**

```python
def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

- [ ] **Step 2: Read and verify the exact pinned mathlib revision**

Parse `lake-manifest.json` as JSON, locate the package named `mathlib`, and require its `rev`/resolved revision to equal:

```python
EXPECTED_MATHLIB_REVISION = "0df444a360eaa60ab8c11dca51a86af692955474"
```

If the manifest representation uses a field name other than `rev`, inspect the existing pinned manifest and bind the exact resolved commit field; do not infer from a branch/tag name. Mismatch raises `ValueError("MATHLIB_REVISION_MISMATCH")`.

- [ ] **Step 3: Build the engine manifest from exact bytes**

Manifest keys are exactly:

```python
ENGINE_FIELDS = {
    "schema",
    "git_head_sha",
    "oracle_source_sha256",
    "bridge_source_sha256",
    "nat_homology_source_sha256",
    "lean_toolchain_sha256",
    "lake_manifest_sha256",
    "mathlib_revision",
    "oracle_binary_sha256",
}
```

Set `schema = "MATHLIB_RUNTIME_ENGINE_ID_V1"` and compute:

```python
engine_sha256 = sha256_bytes(canonical_json_bytes(engine_manifest))
```

The orchestrator accepts `git_head_sha` only as an explicit CLI argument supplied by CI. It does not call the network and does not trust a mutable branch name as authority.

- [ ] **Step 4: Implement strict oracle execution**

```python
argv = [str(binary)]
if negative_control:
    argv.append("--negative-control")
proc = subprocess.run(
    argv,
    cwd=binary.parent,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=30,
    check=False,
    shell=False,
)
```

Fail closed on timeout, non-zero exit, non-empty stderr, empty stdout, or multiple lines. Return raw stdout bytes only after validation.

- [ ] **Step 5: Implement strict oracle schema and semantic checks**

Require exact fields and exact positive/negative frozen matrices from the design spec. Positive additionally requires:

```text
custom matrix == expected matrix
mathlib matrix == expected matrix
custom matrix == mathlib matrix
matrix has exactly two equivalence classes
all four representatives present
16/16 ordered pairs represented
```

Negative requires:

```text
custom matrix == positive expected matrix
mathlib matrix == singleton expected negative matrix
custom matrix != mathlib matrix
class_equal == false
negative_control == true
```

- [ ] **Step 6: Run the Python test suite and confirm GREEN for engine/schema/execution helpers**

```bash
python -m unittest discover -s formal/namespace-safe-eq64/runtime -p 'test_runtime_bind_canary.py' -v
```

Expected: all tests implemented through Task 6 pass. Replay/receipt tests added in the next task are not yet present.

- [ ] **Step 7: Commit the engine identity/execution layer**

```bash
git add formal/namespace-safe-eq64/runtime/runtime_bind_canary.py
git commit -m "feat(formal): bind runtime oracle to exact engine identity"
```

---

### Task 7: RED → GREEN negative control, identical replay, deterministic receipt, and fresh rehash

**Files:**
- Modify: `formal/namespace-safe-eq64/runtime/test_runtime_bind_canary.py`
- Modify: `formal/namespace-safe-eq64/runtime/runtime_bind_canary.py`

**Interfaces:**
- Produces final `run_canary(...)` result and deterministic receipt schema `MATHLIB_FORMAL_RUNTIME_BIND_RECEIPT_V1`.

- [ ] **Step 1: Add failing replay and receipt tests first**

Add tests that inject a fake executable runner or call a small deterministic fixture command only at the process boundary, while testing receipt logic with real bytes. Required assertions:

```python
self.assertEqual(run_a, run_b)
self.assertNotEqual(run_a, negative)
self.assertEqual(receipt_a_bytes, receipt_b_bytes)
self.assertEqual(sha256_bytes(receipt_a_bytes), sha256_bytes(receipt_b_bytes))
```

Add one-byte mutation tests proving `verify_receipt_dependencies` rejects changed oracle source, bridge source, nat-homology source, toolchain, manifest, binary, witness descriptor, and positive output. Each mismatch error names the field, e.g. `DEPENDENCY_SHA256_MISMATCH:oracle_binary_sha256`.

- [ ] **Step 2: Run tests and confirm RED**

```bash
python -m unittest discover -s formal/namespace-safe-eq64/runtime -p 'test_runtime_bind_canary.py' -v
```

Expected: failures only because replay/receipt/readback functions are missing or incomplete.

- [ ] **Step 3: Define a canonical witness descriptor owned by the orchestrator**

Use literal canonical data:

```python
WITNESS = {
    "schema": "MATHLIB_RUNTIME_WITNESS_V1",
    "name": "ZMOD4_H1_BOUNDARY_TIMES_2",
    "degree": 1,
    "carrier": "ZMod 4",
    "incoming_boundary": "mul_2",
    "outgoing_boundary": "zero",
    "representatives": [0, 1, 2, 3],
}
```

Hash `canonical_json_bytes(WITNESS)` into `witness_sha256`. This descriptor is metadata for receipt binding only; it does not compute homology.

- [ ] **Step 4: Implement deterministic receipt creation**

Receipt keys are exactly:

```python
RECEIPT_FIELDS = {
    "schema",
    "formal_gate",
    "authority_scope",
    "git_head_sha",
    "engine_sha256",
    "oracle_binary_sha256",
    "mathlib_revision",
    "witness_sha256",
    "positive_output_sha256",
    "negative_output_sha256",
    "custom_vs_mathlib_class_equal",
    "negative_control_detected",
    "replay_output_equal",
    "receipt_replay_equal",
    "general_runtime_admission",
    "global_bind",
    "pointer_promotion",
    "production_readiness",
}
```

Required fixed values:

```python
"schema": "MATHLIB_FORMAL_RUNTIME_BIND_RECEIPT_V1"
"formal_gate": "PASS_MATHLIB_HOMOLOGICAL_COMPLEX_INTEROPERABILITY_AND_HOMOLOGY_BRIDGE_V1"
"authority_scope": "ISOLATED_CI_CANARY_ONLY"
"custom_vs_mathlib_class_equal": True
"negative_control_detected": True
"replay_output_equal": True
"receipt_replay_equal": True
"general_runtime_admission": False
"global_bind": False
"pointer_promotion": False
"production_readiness": False
```

Receipt serialization is `canonical_json_bytes(receipt) + b"\n"`.

- [ ] **Step 5: Implement exact run order without rebuild between A and B**

`run_canary` performs:

```text
verify pins/source inputs
hash prebuilt oracle binary
positive A
negative control
positive B
require raw A == raw B
require canonical parsed A == canonical parsed B
build receipt A
build receipt B independently from the same freshly read dependencies
require receipt A bytes == receipt B bytes
persist engine_manifest.json, positive_a.json, negative.json, positive_b.json, receipt.json
freshly reopen all persisted files and every bound dependency
rehash and verify
```

The function must not invoke `lake build` between A and B. Build happens before `run_canary`, so replay proves execution determinism of the same binary SHA.

- [ ] **Step 6: Implement authority ceiling validation**

Any receipt with one of these values true is rejected:

```text
general_runtime_admission
global_bind
pointer_promotion
production_readiness
```

No separate `runtime_bind=true` field is introduced. Positive authority exists only through `authority_scope = ISOLATED_CI_CANARY_ONLY`.

- [ ] **Step 7: Run all Python tests and confirm GREEN**

```bash
python -m unittest discover -s formal/namespace-safe-eq64/runtime -p 'test_runtime_bind_canary.py' -v
```

Expected: exit 0 with all contract, mutation, negative-control, replay, receipt-equality, and fresh-rehash tests passing.

- [ ] **Step 8: Run the actual built Lean oracle through the orchestrator locally/CI runner**

From `formal/namespace-safe-eq64` after `lake build runtimeBindOracle`:

```bash
python runtime/runtime_bind_canary.py \
  --repo-root ../.. \
  --formal-root . \
  --git-head-sha "$(git rev-parse HEAD)" \
  --oracle-binary .lake/build/bin/runtimeBindOracle \
  --output-dir /tmp/mathlib-runtime-bind-canary
```

If the script is designed to resolve `repo-root` from `formal-root`, keep only one unambiguous root argument; the final CLI must have one canonical invocation documented in `--help` and CI.

- [ ] **Step 9: Commit replay/receipt implementation**

```bash
git add formal/namespace-safe-eq64/runtime/runtime_bind_canary.py formal/namespace-safe-eq64/runtime/test_runtime_bind_canary.py
git commit -m "feat(formal): add replay-stable runtime bind receipt"
```

---

### Task 8: Add the dedicated exact-head GitHub Actions gate

**Files:**
- Create: `.github/workflows/mathlib-runtime-bind-canary.yml`
- No changes to existing RCCA workflow.

**Interfaces:**
- Consumes: PR exact head SHA and the committed runtime-bind package.
- Produces: one required-style CI result named `Mathlib Runtime Bind Canary` plus uploaded diagnostic artifacts only if the repository's existing workflow policy permits free GitHub artifact storage. Artifact upload is non-authoritative; PASS comes from job execution and hashes.

- [ ] **Step 1: Write the workflow with exact PR-head checkout**

Use the existing namespace-safe workflow's checkout/toolchain pattern. The job must checkout `${{ github.event.pull_request.head.sha }}` for PR events and then assert:

```bash
test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"
```

- [ ] **Step 2: Verify the formal antecedent on the same head**

Run:

```bash
cd formal/namespace-safe-eq64
lake build
lake env lean NamespaceSafeEQ64Test.lean
lake env lean RuntimeBindOracleTest.lean
```

Retain the existing proof-escape scanner pattern used by `namespace-safe-eq64.yml`; do not duplicate it with weaker regex semantics. If the scanner is embedded inline in the existing workflow, copy its exact command unchanged.

- [ ] **Step 3: Verify the pinned mathlib revision explicitly**

Add a small Python/JSON check against `lake-manifest.json` requiring exactly:

```text
0df444a360eaa60ab8c11dca51a86af692955474
```

This is separate from merely building against whatever Lake resolved.

- [ ] **Step 4: Run the Python TDD suite**

```bash
python -m unittest discover -s formal/namespace-safe-eq64/runtime -p 'test_runtime_bind_canary.py' -v
```

- [ ] **Step 5: Build exactly one oracle binary and hash it**

```bash
cd formal/namespace-safe-eq64
lake build runtimeBindOracle
sha256sum .lake/build/bin/runtimeBindOracle
```

No rebuild occurs between positive A and positive B.

- [ ] **Step 6: Execute the orchestrator once for the complete A/negative/B sequence**

Canonical CI command:

```bash
python runtime/runtime_bind_canary.py \
  --git-head-sha "$GITHUB_SHA" \
  --oracle-binary .lake/build/bin/runtimeBindOracle \
  --output-dir "$RUNNER_TEMP/mathlib-runtime-bind-canary"
```

If PR checkout uses a dedicated `PR_HEAD_SHA` variable instead of `GITHUB_SHA`, pass the value already proven equal to `git rev-parse HEAD`.

- [ ] **Step 7: Independently inspect the persisted receipt in a new process**

Add CLI mode:

```bash
python runtime/runtime_bind_canary.py verify \
  --git-head-sha "$PR_HEAD_SHA" \
  --oracle-binary .lake/build/bin/runtimeBindOracle \
  --output-dir "$RUNNER_TEMP/mathlib-runtime-bind-canary"
```

The `verify` path must read, parse, and rehash persisted bytes; it cannot reuse in-memory objects from the generation process.

- [ ] **Step 8: Assert authority ceilings in CI with exact string/JSON checks**

The verifier must end with all four false:

```text
GENERAL_RUNTIME_ADMISSION=false
GLOBAL_BIND=false
POINTER_PROMOTION=false
PRODUCTION_READINESS=false
```

- [ ] **Step 9: Commit the workflow**

```bash
git add .github/workflows/mathlib-runtime-bind-canary.yml
git commit -m "ci(formal): gate isolated mathlib runtime bind canary"
```

---

### Task 9: Fresh same-head verification with existing Formal CI and RCCA

**Files:**
- No implementation changes unless a verification failure identifies a concrete defect.

**Interfaces:**
- Consumes: exact final candidate commit SHA.
- Produces the evidence required for the only permitted PASS claim.

- [ ] **Step 1: Freeze the candidate SHA without promoting or merging**

```bash
CANDIDATE_SHA="$(git rev-parse HEAD)"
echo "$CANDIDATE_SHA"
```

PR #20 remains draft.

- [ ] **Step 2: Require the new runtime-bind workflow SUCCESS on `CANDIDATE_SHA`**

Verify the workflow run reports `head_sha == CANDIDATE_SHA` and every mandatory step is success:

```text
exact checkout
formal build
formal theorem harness
proof-escape rejection
pinned mathlib revision
Python runtime tests
oracle build
engine SHA materialization
positive A
negative control
positive B
output equality
receipt equality
fresh readback
claim-ceiling assertions
```

- [ ] **Step 3: Require `Namespace-Safe EQ64 Formal Reference Gate` SUCCESS on the same SHA**

Do not accept a prior nearby commit. Required same-head evidence includes build, pinned revision, theorem harness/proof-escape, Python formal-reference tests, and non-actuating markers.

- [ ] **Step 4: Require `RCCA Required Status Provider Gate V1` SUCCESS on the same SHA**

Require both deterministic builds, proof-escape scanner test, regression, coverage, exact artifact equality, and aggregate provider gate success.

- [ ] **Step 5: Read back the final persisted runtime receipt**

Record exact values:

```text
GIT_HEAD_SHA
ENGINE_SHA256
ORACLE_BINARY_SHA256
MATHLIB_REVISION
WITNESS_SHA256
POSITIVE_OUTPUT_SHA256
NEGATIVE_OUTPUT_SHA256
RECEIPT_SHA256
```

Verify all four upper authority ceilings remain false.

- [ ] **Step 6: Only if every mandatory item above is green, report exactly**

```text
PASS_MATHLIB_FORMAL_EQUIVALENCE__AUTHORITATIVE_RUNTIME_BIND_CANARY_V1

FORMAL_EQUIVALENCE               = PASS
EXACT_ENGINE_SHA                 = PASS
CUSTOM_VS_MATHLIB_CLASS_EQUAL    = PASS
NEGATIVE_CONTROL                 = PASS
IDENTICAL_REPLAY                 = PASS
RECEIPT_EQUALITY                 = PASS
FRESH_READBACK                   = PASS
FORMAL_CI_SAME_HEAD              = PASS
RCCA_SAME_HEAD                   = PASS
AUTHORITATIVE_RUNTIME_BIND_SCOPE = ISOLATED_CI_CANARY_ONLY
GENERAL_RUNTIME_ADMISSION        = FALSE
GLOBAL_BIND                      = FALSE
POINTER_PROMOTION                = FALSE
PRODUCTION_READINESS             = FALSE
```

Any missing or non-green item yields `STATUS = HOLD` with `FIRST_MISSING_PROOF` naming the earliest missing mandatory evidence. Do not partially promote the claim.

---

## Plan Self-Review

### Spec coverage

- Python orchestrator + pinned Lean authoritative oracle: Tasks 2–8.
- Exact source/toolchain/mathlib/binary SHA identity: Task 6 and CI Task 8.
- Frozen non-trivial `ZMod 4` degree-1 witness: Tasks 2–4.
- Independent custom vs mathlib class-equality matrices: Tasks 2–3.
- Literal 4×4 expected matrix and non-triviality: Tasks 2, 3, 6.
- Controlled negative route: Tasks 4, 7, 8.
- Positive A / negative / positive B replay without rebuild: Task 7 and Task 8.
- Byte-identical outputs and receipts: Task 7.
- Fresh dependency readback/rehash: Task 7 and Task 8.
- Same-head Formal CI + RCCA: Task 9.
- Claim ceiling isolation: Global Constraints, Tasks 7–9.
- ZERO_SPEND/no network/no secrets/remote actuation: Global Constraints and CI design.

### Placeholder scan

This plan intentionally contains no `TBD`, `TODO`, “implement later”, unspecified edge-case bucket, or generic “write tests” step. Where a pinned API elaboration may require a syntax-equivalent Lean construction, the mathematical witness and acceptable API boundary are fixed and may not be weakened.

### Type/interface consistency

- Lean public names used by later tasks are introduced in Tasks 2–4.
- Python public functions used by later tasks are fixed in Task 5 and implemented in Tasks 6–7.
- Receipt schema and field names are fixed once in Task 7 and consumed unchanged in Tasks 8–9.
- The authority field is `authority_scope = ISOLATED_CI_CANARY_ONLY`; no general `runtime_bind=true` is introduced.

## Execution Boundary

The plan itself authorizes no implementation. Execution starts only after choosing an execution mode. The first executable action is Task 1 RED, not production code.
