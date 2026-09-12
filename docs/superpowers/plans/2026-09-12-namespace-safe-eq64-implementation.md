# Namespace-Safe EQ64 Formal/Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a fail-closed formal/reference subsystem that permits B6/Q6 structural reuse while preventing any semantic EQ64 crosswalk from becoming PASS without explicit C1-C11 evidence.

**Architecture:** Keep the subsystem isolated under `formal/namespace-safe-eq64/`. Lean 4 proves the non-inference and structural obligations; a Python standard-library reference engine performs exhaustive 64-state and 720-permutation conformance checks, synthetic positive/negative controls, and content-addressed receipt generation. No runtime consumer is wired in this plan.

**Tech Stack:** Lean 4.33.1, Lake, Python 3 standard library (`dataclasses`, `enum`, `hashlib`, `itertools`, `json`, `pathlib`, `unittest`), JSON fixtures/schemas, SHA256.

**Spec:** `docs/superpowers/specs/2026-09-12-namespace-safe-eq64-design.md`

## Global Constraints

- `FORMAL SPEC -> REFERENCE ENGINE -> 720 ADVERSARIAL CANARY -> POSITIVE CONTROL -> CONTENT-ADDRESSED RECEIPT` is the mandatory order.
- `RUNTIME_BIND = FALSE` throughout this plan.
- No active runtime imports or consumer wiring.
- No production dependency or engine auto-registration.
- No pointer mutation/promotion.
- No global authority bind or runtime admission.
- No empirical or physical validation claim.
- `STRUCTURAL REUSE MAY CROSS NAMESPACES. SEMANTIC MEANINGS MAY NOT CROSS NAMESPACES WITHOUT C1-C11 PROOF.`
- Bare `EQ64` semantic references are policy DENY.
- Missing evidence yields HOLD; explicit contradiction/policy conflict yields DENY; unknown is never coerced to PASS.
- No weighted score may override a failed mandatory gate.
- Maximum success claim: `PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT`.

---

## File Structure

Create the following subsystem. Do not modify application/runtime files in this phase.

```text
formal/namespace-safe-eq64/
├── NamespaceSafeEQ64.lean              # typed model + theorem obligations
├── NamespaceSafeEQ64Test.lean          # compile-time theorem checks and concrete countermodels
├── lakefile.lean                       # isolated Lean package
├── lean-toolchain                      # pin Lean 4.33.1
├── README.md                           # exact build/test/readback commands and claim ceiling
├── reference/
│   ├── namespace_safe_engine.py        # typed TRI engine; structure + semantics
│   ├── permutation_canary_720.py       # exhaustive real and synthetic permutation runner
│   └── receipt.py                      # canonical JSON + SHA256 bundle/readback verification
├── fixtures/
│   ├── ess_eq64_6d_kernel.json         # canonical ESS namespace fixture
│   ├── x_aiprbg_6gate.json             # audit namespace fixture, no semantic crosswalk evidence
│   ├── synthetic_exact_a.json          # synthetic source with complete exact mapping evidence
│   └── synthetic_exact_b.json          # synthetic target with matching evidence
├── schema/
│   ├── namespace.schema.json           # declarative namespace contract
│   ├── crosswalk_evidence.schema.json  # C1-C11 evidence contract
│   └── canary_receipt.schema.json      # receipt field/type contract
└── tests/
    ├── test_structure.py               # 64-state, encode/decode, meet/join, Hamming, polarity
    ├── test_semantic_gate.py           # PASS/HOLD/DENY policy matrix
    ├── test_720_canary.py              # 720/720 real negative canary
    └── test_positive_control.py        # exactly 1 PASS, 719 DENY synthetic control
```

Generated receipts go to a caller-supplied output path (for example `/tmp/eq64_namespace_safe_canary_receipt.json`) and are not committed by this plan.

---

### Task 1: Bootstrap the isolated Lean package and typed namespace model

**Files:**
- Create: `formal/namespace-safe-eq64/lean-toolchain`
- Create: `formal/namespace-safe-eq64/lakefile.lean`
- Create: `formal/namespace-safe-eq64/NamespaceSafeEQ64.lean`
- Create: `formal/namespace-safe-eq64/NamespaceSafeEQ64Test.lean`

**Interfaces:**
- Consumes: no implementation files; only the approved spec.
- Produces: `NamespaceId`, `Polarity`, `StructuralClass`, `AxisSchema`, `SemanticEvidence`, `CrosswalkCandidate`, `Tri`, `ExactSemanticAuthorized`, and `SemanticRequestAllowed` for later theorem tasks.

- [ ] **Step 1: Write the package pin and Lake manifest**

`formal/namespace-safe-eq64/lean-toolchain`:

```text
leanprover/lean4:v4.33.1
```

`formal/namespace-safe-eq64/lakefile.lean`:

```lean
import Lake
open Lake DSL

package namespaceSafeEq64 where

@[default_target]
lean_lib NamespaceSafeEQ64
```

- [ ] **Step 2: Write the initial failing Lean test**

Create `NamespaceSafeEQ64Test.lean`:

```lean
import NamespaceSafeEQ64
open NamespaceSafeEQ64

#check NamespaceId
#check Polarity
#check StructuralClass
#check AxisSchema
#check SemanticEvidence
#check CrosswalkCandidate
#check Tri
#check ExactSemanticAuthorized
#check SemanticRequestAllowed
```

- [ ] **Step 3: Run the test and verify it fails before definitions exist**

Run:

```bash
cd formal/namespace-safe-eq64
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: FAIL with unknown identifier errors for the checked names.

- [ ] **Step 4: Implement the minimal typed model**

Create `NamespaceSafeEQ64.lean`:

```lean
import Std

namespace NamespaceSafeEQ64

set_option autoImplicit false

inductive NamespaceId where
  | essEq64Kernel
  | aipRbgDiagnostic
  | syntheticA
  | syntheticB
  | bareEq64
  | other (name : String)
  deriving DecidableEq, Repr

inductive Polarity where
  | risk
  | protect
  | neutral
  deriving DecidableEq, Repr

inductive StructuralClass where
  | b6q6
  deriving DecidableEq, Repr

inductive Tri where
  | pass
  | hold
  | deny
  deriving DecidableEq, Repr

abbrev State6 := Fin 6 → Bool
abbrev AxisSchema := Fin 6 → String
abbrev PolaritySchema := Fin 6 → Polarity

structure NamespaceSpec where
  id : NamespaceId
  axes : AxisSchema
  polarity : PolaritySchema
  structuralClass : StructuralClass
  claimCeiling : String

structure SemanticEvidence where
  c1SourceIdentity : Bool
  c2StructuralClass : Bool
  c3AxisCompleteness : Bool
  c4Polarity : Bool
  c5ConflictFree : Bool
  c6BijectionCandidate : Bool
  c7AxisEvidence : Bool
  c8OrderSemantics : Bool
  c9NoPostHocSelection : Bool
  c10GovernanceScope : Bool
  c11ClaimCeiling : Bool
  deriving Repr

structure CrosswalkCandidate where
  source : NamespaceId
  target : NamespaceId
  permutation : Fin 6 → Fin 6
  evidence : SemanticEvidence


def SemanticRequestAllowed (c : CrosswalkCandidate) : Prop :=
  c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64


def ExactSemanticAuthorized (c : CrosswalkCandidate) : Prop :=
  SemanticRequestAllowed c ∧
  c.evidence.c1SourceIdentity = true ∧
  c.evidence.c2StructuralClass = true ∧
  c.evidence.c3AxisCompleteness = true ∧
  c.evidence.c4Polarity = true ∧
  c.evidence.c5ConflictFree = true ∧
  c.evidence.c6BijectionCandidate = true ∧
  c.evidence.c7AxisEvidence = true ∧
  c.evidence.c8OrderSemantics = true ∧
  c.evidence.c9NoPostHocSelection = true ∧
  c.evidence.c10GovernanceScope = true ∧
  c.evidence.c11ClaimCeiling = true

end NamespaceSafeEQ64
```

- [ ] **Step 5: Run Lean test and verify the typed model passes**

Run:

```bash
cd formal/namespace-safe-eq64
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: PASS, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add formal/namespace-safe-eq64/{lean-toolchain,lakefile.lean,NamespaceSafeEQ64.lean,NamespaceSafeEQ64Test.lean}
git commit -m "feat: add namespace-safe EQ64 formal types"
```

---

### Task 2: Prove B6 structural preservation under coordinate permutations

**Files:**
- Modify: `formal/namespace-safe-eq64/NamespaceSafeEQ64.lean`
- Modify: `formal/namespace-safe-eq64/NamespaceSafeEQ64Test.lean`

**Interfaces:**
- Consumes: `State6` from Task 1.
- Produces: `bMeet`, `bJoin`, `applyPerm`, `HammingOne`, `coordinate_permutation_preserves_B6_structure`, and `coordinate_permutation_preserves_Q6_hamming`.

- [ ] **Step 1: Add failing theorem checks**

Append to `NamespaceSafeEQ64Test.lean`:

```lean
#check bMeet
#check bJoin
#check applyPerm
#check HammingOne
#check coordinate_permutation_preserves_B6_structure
#check coordinate_permutation_preserves_Q6_hamming
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: FAIL because the new structural names are undefined.

- [ ] **Step 3: Add B6 operations and permutation map**

Append inside `namespace NamespaceSafeEQ64` before its final `end`:

```lean
def bMeet (a b : State6) : State6 := fun i => a i && b i

def bJoin (a b : State6) : State6 := fun i => a i || b i

def applyPerm (p : Equiv.Perm (Fin 6)) (s : State6) : State6 :=
  fun i => s (p.symm i)

/-- Hamming-distance-one adjacency without importing a heavier algebra library. -/
def HammingOne (a b : State6) : Prop :=
  ∃ j : Fin 6, a j ≠ b j ∧ ∀ i : Fin 6, i ≠ j → a i = b i
```

- [ ] **Step 4: Add the B6 preservation theorem**

```lean
theorem coordinate_permutation_preserves_B6_structure
    (p : Equiv.Perm (Fin 6)) (a b : State6) :
    applyPerm p (bMeet a b) = bMeet (applyPerm p a) (applyPerm p b) ∧
    applyPerm p (bJoin a b) = bJoin (applyPerm p a) (applyPerm p b) := by
  constructor <;> funext i <;> rfl
```

- [ ] **Step 5: Add the Q6 Hamming-one preservation theorem**

```lean
theorem coordinate_permutation_preserves_Q6_hamming
    (p : Equiv.Perm (Fin 6)) (a b : State6)
    (h : HammingOne a b) :
    HammingOne (applyPerm p a) (applyPerm p b) := by
  rcases h with ⟨j, hjdiff, hjrest⟩
  refine ⟨p j, ?_, ?_⟩
  · simpa [applyPerm] using hjdiff
  · intro i hi
    have hpre : p.symm i ≠ j := by
      intro hEq
      apply hi
      exact p.injective (by simpa using congrArg p hEq)
    exact hjrest (p.symm i) hpre
```

If Lean rejects the `simpa` bridge because of simplifier normalization, use the equivalent explicit equalities below, not a new axiom:

```lean
  · change a (p.symm (p j)) ≠ b (p.symm (p j))
    simpa using hjdiff
```

- [ ] **Step 6: Run Lean and verify both theorem checks pass**

```bash
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: PASS, exit code 0, no `sorry` warnings.

- [ ] **Step 7: Commit**

```bash
git add formal/namespace-safe-eq64/NamespaceSafeEQ64*.lean
git commit -m "feat: prove B6 Q6 permutation preservation"
```

---

### Task 3: Prove semantic non-inference and fail-closed evidence obligations

**Files:**
- Modify: `formal/namespace-safe-eq64/NamespaceSafeEQ64.lean`
- Modify: `formal/namespace-safe-eq64/NamespaceSafeEQ64Test.lean`

**Interfaces:**
- Consumes: `CrosswalkCandidate`, `ExactSemanticAuthorized`.
- Produces: `no_semantic_authorization_from_structure_alone`, `missing_axis_evidence_blocks_exact_crosswalk`, `polarity_conflict_blocks_exact_crosswalk`, `namespace_identity_required`.

- [ ] **Step 1: Add failing theorem checks**

Append:

```lean
#check no_semantic_authorization_from_structure_alone
#check missing_axis_evidence_blocks_exact_crosswalk
#check polarity_conflict_blocks_exact_crosswalk
#check namespace_identity_required
```

- [ ] **Step 2: Run and verify failure**

```bash
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: FAIL with unknown theorem identifiers.

- [ ] **Step 3: Prove missing axis evidence blocks exact authorization**

Add:

```lean
theorem missing_axis_evidence_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hMissing : c.evidence.c7AxisEvidence = false) :
    ¬ ExactSemanticAuthorized c := by
  intro h
  rcases h with ⟨_, _, _, _, _, _, _, hAxis, _, _, _, _⟩
  simp [hMissing] at hAxis
```

- [ ] **Step 4: Prove polarity conflict blocks exact authorization**

```lean
theorem polarity_conflict_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hConflict : c.evidence.c4Polarity = false) :
    ¬ ExactSemanticAuthorized c := by
  intro h
  rcases h with ⟨_, _, _, _, hPolarity, _, _, _, _, _, _, _⟩
  simp [hConflict] at hPolarity
```

- [ ] **Step 5: Prove namespace identity is mandatory**

```lean
theorem namespace_identity_required
    (c : CrosswalkCandidate)
    (h : ExactSemanticAuthorized c) :
    c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64 :=
  h.1
```

- [ ] **Step 6: Prove structure alone cannot mint semantic authority**

```lean
theorem no_semantic_authorization_from_structure_alone
    (c : CrosswalkCandidate)
    (structuralIso : Prop)
    (hStructural : structuralIso)
    (hNoAxisEvidence : c.evidence.c7AxisEvidence = false) :
    ¬ ExactSemanticAuthorized c := by
  exact missing_axis_evidence_blocks_exact_crosswalk c hNoAxisEvidence
```

The intentionally unused `hStructural` documents the theorem's boundary: structural truth does not discharge the missing semantic-evidence obligation. Do not replace this with an axiom or `sorry`.

- [ ] **Step 7: Add a concrete bare-EQ64 countermodel**

Append to `NamespaceSafeEQ64Test.lean`:

```lean
def allTrueEvidence : SemanticEvidence := {
  c1SourceIdentity := true,
  c2StructuralClass := true,
  c3AxisCompleteness := true,
  c4Polarity := true,
  c5ConflictFree := true,
  c6BijectionCandidate := true,
  c7AxisEvidence := true,
  c8OrderSemantics := true,
  c9NoPostHocSelection := true,
  c10GovernanceScope := true,
  c11ClaimCeiling := true
}

def identityFin6 : Fin 6 → Fin 6 := fun i => i

def bareCandidate : CrosswalkCandidate := {
  source := .bareEq64,
  target := .essEq64Kernel,
  permutation := identityFin6,
  evidence := allTrueEvidence
}

example : ¬ ExactSemanticAuthorized bareCandidate := by
  intro h
  exact h.1.1 rfl
```

- [ ] **Step 8: Run Lean with an explicit `sorry` scan**

```bash
lake env lean NamespaceSafeEQ64Test.lean
! grep -R "\bsorry\b\|\badmit\b\|\baxiom\b" -n NamespaceSafeEQ64.lean NamespaceSafeEQ64Test.lean
```

Expected: both commands exit 0; scan prints no matches.

- [ ] **Step 9: Commit**

```bash
git add formal/namespace-safe-eq64/NamespaceSafeEQ64*.lean
git commit -m "feat: prove namespace semantic non-inference"
```

---

### Task 4: Add canonical fixtures, schemas, and the structural reference engine

**Files:**
- Create: `formal/namespace-safe-eq64/fixtures/ess_eq64_6d_kernel.json`
- Create: `formal/namespace-safe-eq64/fixtures/x_aiprbg_6gate.json`
- Create: `formal/namespace-safe-eq64/schema/namespace.schema.json`
- Create: `formal/namespace-safe-eq64/schema/crosswalk_evidence.schema.json`
- Create: `formal/namespace-safe-eq64/reference/namespace_safe_engine.py`
- Create: `formal/namespace-safe-eq64/tests/test_structure.py`

**Interfaces:**
- Produces Python API: `Tri`, `load_namespace`, `validate_namespace`, `all_states`, `encode_state`, `decode_state`, `normalize_polarity`, `apply_permutation`, `meet`, `join`, `hamming_distance`, `check_structural_mapping`.

- [ ] **Step 1: Write the real namespace fixtures**

`fixtures/ess_eq64_6d_kernel.json`:

```json
{
  "namespace_id": "ESS_EQ64_6D_KERNEL",
  "structural_class": "B6_Q6",
  "axes": ["energy_load", "volatility", "coherence", "phase_stability", "transient_headroom", "lock_margin"],
  "polarity": ["risk", "risk", "protect", "protect", "protect", "protect"],
  "claim_ceiling": "CANONICAL_STRUCTURAL_EQ64_REFERENCE"
}
```

`fixtures/x_aiprbg_6gate.json`:

```json
{
  "namespace_id": "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
  "structural_class": "B6_Q6",
  "axes": ["Authority", "Identity", "Provenance", "Runtime", "Readback", "Governance"],
  "polarity": ["protect", "protect", "protect", "protect", "protect", "protect"],
  "claim_ceiling": "AUDIT_DIAGNOSTIC_ONLY"
}
```

- [ ] **Step 2: Write strict declarative schemas**

`schema/namespace.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["namespace_id", "structural_class", "axes", "polarity", "claim_ceiling"],
  "properties": {
    "namespace_id": {"type": "string", "minLength": 1},
    "structural_class": {"const": "B6_Q6"},
    "axes": {"type": "array", "minItems": 6, "maxItems": 6, "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
    "polarity": {"type": "array", "minItems": 6, "maxItems": 6, "items": {"enum": ["risk", "protect", "neutral"]}},
    "claim_ceiling": {"type": "string", "minLength": 1}
  }
}
```

`schema/crosswalk_evidence.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["criteria", "axis_equivalences", "exact_mapping"],
  "properties": {
    "criteria": {
      "type": "object",
      "additionalProperties": false,
      "required": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11"],
      "properties": {
        "C1": {"type": "boolean"}, "C2": {"type": "boolean"}, "C3": {"type": "boolean"},
        "C4": {"type": "boolean"}, "C5": {"type": "boolean"}, "C6": {"type": "boolean"},
        "C7": {"type": "boolean"}, "C8": {"type": "boolean"}, "C9": {"type": "boolean"},
        "C10": {"type": "boolean"}, "C11": {"type": "boolean"}
      }
    },
    "axis_equivalences": {"type": "array", "minItems": 0, "maxItems": 6},
    "exact_mapping": {"type": ["array", "null"]}
  }
}
```

- [ ] **Step 3: Write failing structural tests**

Create `tests/test_structure.py`:

```python
import itertools
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))

from namespace_safe_engine import (
    all_states, apply_permutation, check_structural_mapping, decode_state,
    encode_state, hamming_distance, join, load_namespace, meet,
    normalize_polarity, validate_namespace,
)

class StructureTests(unittest.TestCase):
    def setUp(self):
        self.ess = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        self.aip = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")

    def test_fixture_validation(self):
        validate_namespace(self.ess)
        validate_namespace(self.aip)

    def test_64_states_and_roundtrip(self):
        states = all_states()
        self.assertEqual(len(states), 64)
        self.assertEqual(len(set(states)), 64)
        for state in states:
            self.assertEqual(decode_state(encode_state(state)), state)

    def test_normalization_is_involution_for_ess(self):
        for state in all_states():
            self.assertEqual(
                normalize_polarity(self.ess, normalize_polarity(self.ess, state)),
                state,
            )

    def test_identity_structural_mapping(self):
        result = check_structural_mapping(tuple(range(6)))
        self.assertTrue(result["meet_preserved"])
        self.assertTrue(result["join_preserved"])
        self.assertTrue(result["hamming_preserved"])

    def test_hamming_one_examples(self):
        self.assertEqual(hamming_distance((0,0,0,0,0,0), (1,0,0,0,0,0)), 1)
        self.assertEqual(hamming_distance((0,0,0,0,0,0), (1,1,0,0,0,0)), 2)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run tests and verify failure**

```bash
cd formal/namespace-safe-eq64
python -m unittest tests.test_structure -v
```

Expected: FAIL because `namespace_safe_engine` does not exist.

- [ ] **Step 5: Implement the minimal structural engine**

Create `reference/namespace_safe_engine.py`:

```python
from __future__ import annotations

from enum import Enum
import itertools
import json
from pathlib import Path

REGISTERED_NAMESPACES = {
    "ESS_EQ64_6D_KERNEL",
    "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
    "SYNTHETIC_NAMESPACE_A",
    "SYNTHETIC_NAMESPACE_B",
}

class Tri(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    DENY = "DENY"


def load_namespace(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_namespace(ns: dict) -> None:
    required = {"namespace_id", "structural_class", "axes", "polarity", "claim_ceiling"}
    if set(ns) != required:
        raise ValueError("NAMESPACE_FIELDS_MISMATCH")
    if ns["structural_class"] != "B6_Q6":
        raise ValueError("UNSUPPORTED_STRUCTURAL_CLASS")
    if len(ns["axes"]) != 6 or len(set(ns["axes"])) != 6:
        raise ValueError("AXIS_SCHEMA_NOT_EXACT_6_UNIQUE")
    if len(ns["polarity"]) != 6 or any(p not in {"risk", "protect", "neutral"} for p in ns["polarity"]):
        raise ValueError("POLARITY_SCHEMA_INVALID")


def all_states() -> list[tuple[int, ...]]:
    return list(itertools.product((0, 1), repeat=6))


def encode_state(state: tuple[int, ...]) -> int:
    if len(state) != 6 or any(bit not in (0, 1) for bit in state):
        raise ValueError("STATE_NOT_B6")
    return sum(bit << i for i, bit in enumerate(state))


def decode_state(value: int) -> tuple[int, ...]:
    if value < 0 or value >= 64:
        raise ValueError("STATE_ID_OUT_OF_RANGE")
    return tuple((value >> i) & 1 for i in range(6))


def normalize_polarity(ns: dict, state: tuple[int, ...]) -> tuple[int, ...]:
    validate_namespace(ns)
    if len(state) != 6:
        raise ValueError("STATE_NOT_B6")
    return tuple((1 - bit) if polarity == "risk" else bit for bit, polarity in zip(state, ns["polarity"]))


def _validate_permutation(permutation: tuple[int, ...]) -> None:
    if len(permutation) != 6 or set(permutation) != set(range(6)):
        raise ValueError("INVALID_PERMUTATION")


def apply_permutation(state: tuple[int, ...], permutation: tuple[int, ...]) -> tuple[int, ...]:
    _validate_permutation(permutation)
    return tuple(state[i] for i in permutation)


def meet(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(x & y for x, y in zip(a, b))


def join(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(x | y for x, y in zip(a, b))


def hamming_distance(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return sum(x != y for x, y in zip(a, b))


def check_structural_mapping(permutation: tuple[int, ...]) -> dict:
    _validate_permutation(permutation)
    states = all_states()
    meet_ok = True
    join_ok = True
    hamming_ok = True
    for a in states:
        pa = apply_permutation(a, permutation)
        for b in states:
            pb = apply_permutation(b, permutation)
            meet_ok &= apply_permutation(meet(a, b), permutation) == meet(pa, pb)
            join_ok &= apply_permutation(join(a, b), permutation) == join(pa, pb)
            hamming_ok &= hamming_distance(a, b) == hamming_distance(pa, pb)
    return {
        "meet_preserved": bool(meet_ok),
        "join_preserved": bool(join_ok),
        "hamming_preserved": bool(hamming_ok),
    }
```

- [ ] **Step 6: Run structural tests and verify PASS**

```bash
python -m unittest tests.test_structure -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add formal/namespace-safe-eq64/{fixtures,schema,reference/namespace_safe_engine.py,tests/test_structure.py}
git commit -m "feat: add namespace structural reference engine"
```

---

### Task 5: Implement the semantic TRI gate and policy matrix

**Files:**
- Modify: `formal/namespace-safe-eq64/reference/namespace_safe_engine.py`
- Create: `formal/namespace-safe-eq64/tests/test_semantic_gate.py`

**Interfaces:**
- Produces: `check_semantic_crosswalk(source, target, evidence, permutation)` and `classify_mapping(...)`.

- [ ] **Step 1: Write failing semantic policy tests**

Create `tests/test_semantic_gate.py`:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import Tri, check_semantic_crosswalk, load_namespace

ALL_TRUE = {f"C{i}": True for i in range(1, 12)}
IDENTITY = tuple(range(6))

class SemanticGateTests(unittest.TestCase):
    def setUp(self):
        self.ess = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        self.aip = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")

    def test_real_namespaces_without_axis_evidence_hold(self):
        evidence = {"criteria": {f"C{i}": False for i in range(1, 12)}, "axis_equivalences": [], "exact_mapping": None}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)
        self.assertIn("NO_AXIS_LEVEL_EVIDENCE", result["reason_codes"])

    def test_five_of_six_axis_evidence_holds(self):
        evidence = {"criteria": dict(ALL_TRUE), "axis_equivalences": [{"source": i, "target": i} for i in range(5)], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)

    def test_polarity_conflict_denies(self):
        criteria = dict(ALL_TRUE); criteria["C4"] = False
        evidence = {"criteria": criteria, "axis_equivalences": [{"source": i, "target": i} for i in range(6)], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("POLARITY_CONFLICT", result["reason_codes"])

    def test_post_hoc_selection_denies(self):
        criteria = dict(ALL_TRUE); criteria["C9"] = False
        evidence = {"criteria": criteria, "axis_equivalences": [{"source": i, "target": i} for i in range(6)], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)

    def test_bare_eq64_denies_by_policy(self):
        bare = dict(self.aip); bare["namespace_id"] = "EQ64"
        evidence = {"criteria": dict(ALL_TRUE), "axis_equivalences": [{"source": i, "target": i} for i in range(6)], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(bare, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("DENY_POLICY_BARE_EQ64_FORBIDDEN", result["reason_codes"])

    def test_unknown_namespace_holds(self):
        unknown = dict(self.aip); unknown["namespace_id"] = "UNKNOWN_NAMESPACE"
        evidence = {"criteria": dict(ALL_TRUE), "axis_equivalences": [{"source": i, "target": i} for i in range(6)], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(unknown, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)
        self.assertIn("UNREGISTERED_NAMESPACE", result["reason_codes"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_semantic_gate -v
```

Expected: FAIL because `check_semantic_crosswalk` is undefined.

- [ ] **Step 3: Implement exact HOLD/DENY/PASS policy**

Append to `reference/namespace_safe_engine.py`:

```python
def check_semantic_crosswalk(source: dict, target: dict, evidence: dict, permutation: tuple[int, ...]) -> dict:
    _validate_permutation(permutation)
    source_id = source.get("namespace_id")
    target_id = target.get("namespace_id")

    if source_id == "EQ64" or target_id == "EQ64":
        return {"status": Tri.DENY, "reason_codes": ["DENY_POLICY_BARE_EQ64_FORBIDDEN"]}

    if source_id not in REGISTERED_NAMESPACES or target_id not in REGISTERED_NAMESPACES:
        return {"status": Tri.HOLD, "reason_codes": ["UNREGISTERED_NAMESPACE"]}

    criteria = evidence.get("criteria", {})
    if criteria.get("C4") is False:
        return {"status": Tri.DENY, "reason_codes": ["POLARITY_CONFLICT"]}
    if criteria.get("C5") is False:
        return {"status": Tri.DENY, "reason_codes": ["ALIAS_CONFLICT"]}
    if criteria.get("C9") is False:
        return {"status": Tri.DENY, "reason_codes": ["POST_HOC_SELECTION"]}

    axis_eq = evidence.get("axis_equivalences", [])
    if criteria.get("C7") is not True or len(axis_eq) < 6:
        return {"status": Tri.HOLD, "reason_codes": ["NO_AXIS_LEVEL_EVIDENCE"]}

    required = [f"C{i}" for i in range(1, 12)]
    if any(criteria.get(key) is not True for key in required):
        return {"status": Tri.HOLD, "reason_codes": ["INCOMPLETE_C1_C11_EVIDENCE"]}

    exact = evidence.get("exact_mapping")
    if exact is None:
        return {"status": Tri.HOLD, "reason_codes": ["NO_PREDECLARED_EXACT_MAPPING"]}
    if tuple(exact) != permutation:
        return {"status": Tri.DENY, "reason_codes": ["DENY_EXACT_MAPPING_CONFLICT"]}

    return {"status": Tri.PASS, "reason_codes": []}


def classify_mapping(source: dict, target: dict, evidence: dict, permutation: tuple[int, ...]) -> dict:
    structural = check_structural_mapping(permutation)
    semantic = check_semantic_crosswalk(source, target, evidence, permutation)
    structural_pass = all(structural.values())
    return {
        "structural_status": Tri.PASS if structural_pass else Tri.DENY,
        "semantic_status": semantic["status"],
        "claim_ceiling": "SEMANTIC_EXACT" if semantic["status"] is Tri.PASS else "STRUCTURAL_ONLY",
        "reason_codes": semantic["reason_codes"],
    }
```

- [ ] **Step 4: Run semantic matrix tests**

```bash
python -m unittest tests.test_semantic_gate -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run all Python tests so far**

```bash
python -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add formal/namespace-safe-eq64/reference/namespace_safe_engine.py formal/namespace-safe-eq64/tests/test_semantic_gate.py
git commit -m "feat: add fail-closed semantic crosswalk gate"
```

---

### Task 6: Implement and verify the exhaustive 720-permutation negative canary

**Files:**
- Create: `formal/namespace-safe-eq64/reference/permutation_canary_720.py`
- Create: `formal/namespace-safe-eq64/tests/test_720_canary.py`

**Interfaces:**
- Produces: `run_canary(source, target, evidence) -> dict` with exact summary counts and per-permutation results.

- [ ] **Step 1: Write the failing 720 canary test**

Create `tests/test_720_canary.py`:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary

class Canary720Tests(unittest.TestCase):
    def test_real_namespaces_have_zero_semantic_leakage(self):
        source = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")
        target = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        evidence = {"criteria": {f"C{i}": False for i in range(1, 12)}, "axis_equivalences": [], "exact_mapping": None}
        receipt = run_canary(source, target, evidence)
        self.assertEqual(receipt["permutation_count"], 720)
        self.assertEqual(receipt["structural_pass"], 720)
        self.assertEqual(receipt["semantic_pass"], 0)
        self.assertEqual(receipt["semantic_hold"], 720)
        self.assertEqual(receipt["semantic_deny"], 0)
        self.assertEqual(receipt["unexpected_passes"], [])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_720_canary -v
```

Expected: FAIL because `permutation_canary_720` does not exist.

- [ ] **Step 3: Implement exhaustive runner**

Create `reference/permutation_canary_720.py`:

```python
from __future__ import annotations

import itertools
from namespace_safe_engine import Tri, classify_mapping


def run_canary(source: dict, target: dict, evidence: dict) -> dict:
    results = []
    for permutation in itertools.permutations(range(6)):
        classified = classify_mapping(source, target, evidence, permutation)
        results.append({
            "permutation": list(permutation),
            "structural_status": classified["structural_status"].value,
            "semantic_status": classified["semantic_status"].value,
            "reason_codes": classified["reason_codes"],
        })

    structural_pass = sum(r["structural_status"] == Tri.PASS.value for r in results)
    semantic_pass = sum(r["semantic_status"] == Tri.PASS.value for r in results)
    semantic_hold = sum(r["semantic_status"] == Tri.HOLD.value for r in results)
    semantic_deny = sum(r["semantic_status"] == Tri.DENY.value for r in results)
    unexpected = [r["permutation"] for r in results if r["semantic_status"] == Tri.PASS.value]

    return {
        "permutation_count": len(results),
        "structural_pass": structural_pass,
        "semantic_pass": semantic_pass,
        "semantic_hold": semantic_hold,
        "semantic_deny": semantic_deny,
        "unexpected_passes": unexpected,
        "results": results,
    }
```

- [ ] **Step 4: Run the exhaustive negative canary**

```bash
python -m unittest tests.test_720_canary -v
```

Expected exact assertions: `720 structural PASS`, `0 semantic PASS`, `720 semantic HOLD`, `0 DENY`, `unexpected_passes=[]`.

- [ ] **Step 5: Run a direct count-only smoke command**

```bash
python - <<'PY'
import json, pathlib, sys
root = pathlib.Path('.').resolve()
sys.path.insert(0, str(root / 'reference'))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary
src = load_namespace(root/'fixtures/x_aiprbg_6gate.json')
dst = load_namespace(root/'fixtures/ess_eq64_6d_kernel.json')
ev = {'criteria': {f'C{i}': False for i in range(1,12)}, 'axis_equivalences': [], 'exact_mapping': None}
r = run_canary(src,dst,ev)
print({k:r[k] for k in ('permutation_count','structural_pass','semantic_pass','semantic_hold','semantic_deny','unexpected_passes')})
PY
```

Expected:

```text
{'permutation_count': 720, 'structural_pass': 720, 'semantic_pass': 0, 'semantic_hold': 720, 'semantic_deny': 0, 'unexpected_passes': []}
```

- [ ] **Step 6: Commit**

```bash
git add formal/namespace-safe-eq64/reference/permutation_canary_720.py formal/namespace-safe-eq64/tests/test_720_canary.py
git commit -m "test: add 720 permutation semantic leakage canary"
```

---

### Task 7: Add the synthetic one-positive/719-deny control

**Files:**
- Create: `formal/namespace-safe-eq64/fixtures/synthetic_exact_a.json`
- Create: `formal/namespace-safe-eq64/fixtures/synthetic_exact_b.json`
- Create: `formal/namespace-safe-eq64/tests/test_positive_control.py`

**Interfaces:**
- Consumes: `run_canary` and semantic gate from Tasks 5-6.
- Produces: proof that the gate is selective, not permanently HOLD.

- [ ] **Step 1: Add synthetic namespace fixtures**

`fixtures/synthetic_exact_a.json`:

```json
{
  "namespace_id": "SYNTHETIC_NAMESPACE_A",
  "structural_class": "B6_Q6",
  "axes": ["a0", "a1", "a2", "a3", "a4", "a5"],
  "polarity": ["protect", "protect", "protect", "protect", "protect", "protect"],
  "claim_ceiling": "SYNTHETIC_TEST_ONLY"
}
```

`fixtures/synthetic_exact_b.json`:

```json
{
  "namespace_id": "SYNTHETIC_NAMESPACE_B",
  "structural_class": "B6_Q6",
  "axes": ["b0", "b1", "b2", "b3", "b4", "b5"],
  "polarity": ["protect", "protect", "protect", "protect", "protect", "protect"],
  "claim_ceiling": "SYNTHETIC_TEST_ONLY"
}
```

- [ ] **Step 2: Write the positive-control test**

Create `tests/test_positive_control.py`:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary

class PositiveControlTests(unittest.TestCase):
    def test_exactly_one_predeclared_mapping_passes(self):
        source = load_namespace(ROOT / "fixtures" / "synthetic_exact_a.json")
        target = load_namespace(ROOT / "fixtures" / "synthetic_exact_b.json")
        evidence = {
            "criteria": {f"C{i}": True for i in range(1, 12)},
            "axis_equivalences": [{"source": i, "target": i, "evidence_id": f"SYN-{i}"} for i in range(6)],
            "exact_mapping": [0,1,2,3,4,5],
        }
        receipt = run_canary(source, target, evidence)
        self.assertEqual(receipt["permutation_count"], 720)
        self.assertEqual(receipt["structural_pass"], 720)
        self.assertEqual(receipt["semantic_pass"], 1)
        self.assertEqual(receipt["semantic_hold"], 0)
        self.assertEqual(receipt["semantic_deny"], 719)
        self.assertEqual(receipt["unexpected_passes"], [[0,1,2,3,4,5]])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the positive control**

```bash
python -m unittest tests.test_positive_control -v
```

Expected: PASS with exact count 1/720 semantic PASS and 719/720 DENY.

- [ ] **Step 4: Run the negative and positive canaries together**

```bash
python -m unittest tests.test_720_canary tests.test_positive_control -v
```

Expected: both PASS; real namespaces leak zero semantic PASS; synthetic fixture admits exactly one.

- [ ] **Step 5: Commit**

```bash
git add formal/namespace-safe-eq64/fixtures/synthetic_exact_*.json formal/namespace-safe-eq64/tests/test_positive_control.py
git commit -m "test: add selective semantic positive control"
```

---

### Task 8: Add canonical content-addressed receipts and independent readback

**Files:**
- Create: `formal/namespace-safe-eq64/schema/canary_receipt.schema.json`
- Create: `formal/namespace-safe-eq64/reference/receipt.py`
- Modify: `formal/namespace-safe-eq64/reference/permutation_canary_720.py`
- Modify: `formal/namespace-safe-eq64/tests/test_720_canary.py`
- Modify: `formal/namespace-safe-eq64/tests/test_positive_control.py`

**Interfaces:**
- Produces: `canonical_json_bytes`, `sha256_bytes`, `hash_bundle`, `build_receipt`, `write_receipt`, `readback_receipt`, and a CLI entry point in `permutation_canary_720.py`.

- [ ] **Step 1: Define the strict receipt schema**

Create `schema/canary_receipt.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema", "source_namespace", "target_namespace", "permutation_count", "structural_pass", "semantic_pass", "semantic_hold", "semantic_deny", "unexpected_passes", "fixture_sha256", "engine_sha256", "runner_sha256", "result_sha256", "payload_sha256", "runtime_bind"],
  "properties": {
    "schema": {"const": "EQ64_NAMESPACE_SAFE_CANARY_RECEIPT_V1"},
    "source_namespace": {"type": "string"},
    "target_namespace": {"type": "string"},
    "permutation_count": {"const": 720},
    "structural_pass": {"type": "integer", "minimum": 0, "maximum": 720},
    "semantic_pass": {"type": "integer", "minimum": 0, "maximum": 720},
    "semantic_hold": {"type": "integer", "minimum": 0, "maximum": 720},
    "semantic_deny": {"type": "integer", "minimum": 0, "maximum": 720},
    "unexpected_passes": {"type": "array"},
    "fixture_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "engine_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "runner_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "result_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "payload_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "runtime_bind": {"const": false}
  }
}
```

- [ ] **Step 2: Write failing receipt readback assertions**

Append to `tests/test_720_canary.py` a new test that writes to a temporary directory:

```python
import tempfile
from receipt import build_receipt, readback_receipt, write_receipt

    def test_receipt_roundtrip_is_content_addressed(self):
        source_path = ROOT / "fixtures" / "x_aiprbg_6gate.json"
        target_path = ROOT / "fixtures" / "ess_eq64_6d_kernel.json"
        source = load_namespace(source_path)
        target = load_namespace(target_path)
        evidence = {"criteria": {f"C{i}": False for i in range(1, 12)}, "axis_equivalences": [], "exact_mapping": None}
        result = run_canary(source, target, evidence)
        receipt = build_receipt(ROOT, source_path, target_path, result)
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "receipt.json"
            write_receipt(path, receipt)
            reread = readback_receipt(path)
        self.assertEqual(reread, receipt)
        self.assertFalse(receipt["runtime_bind"])
```

- [ ] **Step 3: Run and verify failure**

```bash
python -m unittest tests.test_720_canary.Canary720Tests.test_receipt_roundtrip_is_content_addressed -v
```

Expected: FAIL because `receipt.py` does not exist.

- [ ] **Step 4: Implement canonical hashes and strict receipt validation**

Create `reference/receipt.py`:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA_NAME = "EQ64_NAMESPACE_SAFE_CANARY_RECEIPT_V1"
HASH_FIELDS = {"fixture_sha256", "engine_sha256", "runner_sha256", "result_sha256", "payload_sha256"}


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_bundle(parts: list[bytes]) -> str:
    framed = b"".join(len(part).to_bytes(8, "big") + part for part in parts)
    return sha256_bytes(framed)


def _validate_receipt_shape(receipt: dict) -> None:
    required = {
        "schema", "source_namespace", "target_namespace", "permutation_count",
        "structural_pass", "semantic_pass", "semantic_hold", "semantic_deny",
        "unexpected_passes", "fixture_sha256", "engine_sha256", "runner_sha256",
        "result_sha256", "payload_sha256", "runtime_bind",
    }
    if set(receipt) != required:
        raise ValueError("RECEIPT_FIELDS_MISMATCH")
    if receipt["schema"] != SCHEMA_NAME or receipt["permutation_count"] != 720:
        raise ValueError("RECEIPT_SCHEMA_OR_COUNT_INVALID")
    if receipt["runtime_bind"] is not False:
        raise ValueError("RUNTIME_BIND_MUST_REMAIN_FALSE")
    if receipt["semantic_pass"] + receipt["semantic_hold"] + receipt["semantic_deny"] != 720:
        raise ValueError("SEMANTIC_COUNT_SUM_INVALID")
    for field in HASH_FIELDS:
        value = receipt[field]
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"INVALID_SHA256:{field}")


def build_receipt(root: Path, source_path: Path, target_path: Path, result: dict) -> dict:
    engine_path = root / "reference" / "namespace_safe_engine.py"
    runner_path = root / "reference" / "permutation_canary_720.py"
    result_core = result["results"]
    payload = {
        "schema": SCHEMA_NAME,
        "source_namespace": json.loads(source_path.read_text(encoding="utf-8"))["namespace_id"],
        "target_namespace": json.loads(target_path.read_text(encoding="utf-8"))["namespace_id"],
        "permutation_count": result["permutation_count"],
        "structural_pass": result["structural_pass"],
        "semantic_pass": result["semantic_pass"],
        "semantic_hold": result["semantic_hold"],
        "semantic_deny": result["semantic_deny"],
        "unexpected_passes": result["unexpected_passes"],
        "fixture_sha256": hash_bundle([source_path.read_bytes(), target_path.read_bytes()]),
        "engine_sha256": sha256_bytes(engine_path.read_bytes()),
        "runner_sha256": sha256_bytes(runner_path.read_bytes()),
        "result_sha256": sha256_bytes(canonical_json_bytes(result_core)),
        "runtime_bind": False,
    }
    receipt = dict(payload)
    receipt["payload_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    _validate_receipt_shape(receipt)
    return receipt


def write_receipt(path: Path, receipt: dict) -> None:
    _validate_receipt_shape(receipt)
    path.write_bytes(canonical_json_bytes(receipt) + b"\n")


def readback_receipt(path: Path) -> dict:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    _validate_receipt_shape(receipt)
    payload = dict(receipt)
    claimed = payload.pop("payload_sha256")
    actual = sha256_bytes(canonical_json_bytes(payload))
    if actual != claimed:
        raise ValueError("PAYLOAD_SHA256_MISMATCH")
    return receipt
```

- [ ] **Step 5: Run receipt roundtrip test**

```bash
python -m unittest tests.test_720_canary.Canary720Tests.test_receipt_roundtrip_is_content_addressed -v
```

Expected: PASS.

- [ ] **Step 6: Add CLI receipt generation to the canary runner**

Append to `reference/permutation_canary_720.py`:

```python
if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    from namespace_safe_engine import load_namespace
    from receipt import build_receipt, write_receipt

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    source = load_namespace(args.source)
    target = load_namespace(args.target)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = run_canary(source, target, evidence)
    receipt = build_receipt(args.root, args.source, args.target, result)
    write_receipt(args.out, receipt)
    print(json.dumps(receipt, sort_keys=True))
```

- [ ] **Step 7: Commit**

```bash
git add formal/namespace-safe-eq64/{schema/canary_receipt.schema.json,reference/receipt.py,reference/permutation_canary_720.py,tests}
git commit -m "feat: add content-addressed namespace canary receipt"
```

---

### Task 9: Execute the full gate, independent readback, and document the bounded claim ceiling

**Files:**
- Create: `formal/namespace-safe-eq64/README.md`
- Modify only if test evidence requires a correction: files created in Tasks 1-8.
- Do not touch runtime/application files.

**Interfaces:**
- Consumes all prior tasks.
- Produces final bounded evidence that all mandatory stages pass while `RUNTIME_BIND=false`.

- [ ] **Step 1: Create two evidence files outside the repository for the real and synthetic runs**

Run:

```bash
cat >/tmp/aiprbg_no_semantic_evidence.json <<'JSON'
{"criteria":{"C1":false,"C2":false,"C3":false,"C4":true,"C5":true,"C6":false,"C7":false,"C8":false,"C9":true,"C10":true,"C11":true},"axis_equivalences":[],"exact_mapping":null}
JSON

cat >/tmp/synthetic_exact_evidence.json <<'JSON'
{"criteria":{"C1":true,"C2":true,"C3":true,"C4":true,"C5":true,"C6":true,"C7":true,"C8":true,"C9":true,"C10":true,"C11":true},"axis_equivalences":[{"source":0,"target":0,"evidence_id":"SYN-0"},{"source":1,"target":1,"evidence_id":"SYN-1"},{"source":2,"target":2,"evidence_id":"SYN-2"},{"source":3,"target":3,"evidence_id":"SYN-3"},{"source":4,"target":4,"evidence_id":"SYN-4"},{"source":5,"target":5,"evidence_id":"SYN-5"}],"exact_mapping":[0,1,2,3,4,5]}
JSON
```

- [ ] **Step 2: Run the Lean formal gate**

```bash
cd formal/namespace-safe-eq64
lake build
lake env lean NamespaceSafeEQ64Test.lean
! grep -R "\bsorry\b\|\badmit\b\|\baxiom\b" -n NamespaceSafeEQ64.lean NamespaceSafeEQ64Test.lean
```

Expected: all exit 0.

- [ ] **Step 3: Run the complete Python TDD suite**

```bash
python -m unittest discover -s tests -v
```

Expected: all tests PASS, including 720 real negative canary and 1/720 synthetic positive control.

- [ ] **Step 4: Generate the real namespace receipt**

```bash
python reference/permutation_canary_720.py \
  --root . \
  --source fixtures/x_aiprbg_6gate.json \
  --target fixtures/ess_eq64_6d_kernel.json \
  --evidence /tmp/aiprbg_no_semantic_evidence.json \
  --out /tmp/eq64_namespace_safe_real_receipt.json
```

Expected summary inside receipt:

```text
permutation_count=720
structural_pass=720
semantic_pass=0
semantic_hold=720
semantic_deny=0
unexpected_passes=[]
runtime_bind=false
```

- [ ] **Step 5: Generate the synthetic positive-control receipt**

```bash
python reference/permutation_canary_720.py \
  --root . \
  --source fixtures/synthetic_exact_a.json \
  --target fixtures/synthetic_exact_b.json \
  --evidence /tmp/synthetic_exact_evidence.json \
  --out /tmp/eq64_namespace_safe_synthetic_receipt.json
```

Expected:

```text
permutation_count=720
structural_pass=720
semantic_pass=1
semantic_hold=0
semantic_deny=719
unexpected_passes=[[0,1,2,3,4,5]]
runtime_bind=false
```

- [ ] **Step 6: Perform independent receipt readback and byte/hash verification in a fresh Python process**

```bash
python - <<'PY'
from pathlib import Path
import hashlib, json, sys
root = Path('.').resolve()
sys.path.insert(0, str(root/'reference'))
from receipt import readback_receipt
for path in [Path('/tmp/eq64_namespace_safe_real_receipt.json'), Path('/tmp/eq64_namespace_safe_synthetic_receipt.json')]:
    raw = path.read_bytes()
    receipt = readback_receipt(path)
    print(path.name, len(raw), hashlib.sha256(raw).hexdigest(), receipt['payload_sha256'], receipt['runtime_bind'])
    assert receipt['runtime_bind'] is False
PY
```

Expected: both files read successfully; exact byte size and file SHA256 are printed; embedded payload SHA256 verifies; `runtime_bind` prints `False` twice.

- [ ] **Step 7: Write the README with exact commands and claim boundary**

Create `README.md` containing:

```markdown
# Namespace-Safe EQ64 Formal/Reference Gate

This subsystem separates abstract B6/Q6 structural equivalence from semantic namespace authority.

## Mandatory verification

```bash
lake build
lake env lean NamespaceSafeEQ64Test.lean
python -m unittest discover -s tests -v
```

The real AIPRBG -> ESS canary must produce 720/720 structural PASS and zero semantic PASS without axis-level evidence. The synthetic control must produce exactly one semantic PASS and 719 DENY.

## Claim ceiling

A fully passing run establishes only:

`PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT`

It does not establish empirical truth, physical correctness, historical semantic equivalence, global authority, general runtime admission, or production readiness.

`RUNTIME_BIND = FALSE` in this package.
```

Use four tildes (`~~~~`) around the outer Markdown snippet if editing through a Markdown renderer that would otherwise nest the code fence incorrectly.

- [ ] **Step 8: Run final regression after README creation**

```bash
lake build
lake env lean NamespaceSafeEQ64Test.lean
python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 9: Confirm the change set contains no runtime wiring**

Run from repository root:

```bash
git diff --name-only main...HEAD
```

Expected: only `formal/namespace-safe-eq64/**`, the approved spec, and this plan. No `app.js`, `model.js`, runtime workflow, pointer, or authority file is changed.

- [ ] **Step 10: Commit the README/final documentation**

```bash
git add formal/namespace-safe-eq64/README.md
git commit -m "docs: document namespace-safe EQ64 verification gate"
```

- [ ] **Step 11: Record the final bounded phase verdict**

Only if Tasks 1-9 all satisfy their exact expected results, report:

```text
LEAN_FORMAL_LAYER = PASS
REFERENCE_ENGINE = PASS
720_NEGATIVE_CANARY = 720/720
SYNTHETIC_POSITIVE = 1/720
SYNTHETIC_CONFLICT_DENY = 719/720
SEMANTIC_LEAKAGE = 0
CONTENT_ADDRESSED_RECEIPT = PASS
RUNTIME_BIND = FALSE
FINAL = PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT
```

Otherwise report `FINAL = HOLD` at the first unmet mandatory gate; do not average or compensate around it.
