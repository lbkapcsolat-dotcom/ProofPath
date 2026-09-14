# Namespace-Safe EQ64 Formal/Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a fail-closed formal/reference subsystem that permits B6/Q6 structural reuse while preventing any semantic EQ64 crosswalk from becoming PASS without explicit C1-C11 evidence.

**Architecture:** Keep the subsystem isolated under `formal/namespace-safe-eq64/`. Lean 4 proves structural preservation and semantic non-inference; a Python standard-library reference engine exhaustively checks all 64 states and all 720 coordinate permutations, runs a one-positive synthetic control, and emits a content-addressed receipt for the real AIPRBG→ESS negative canary. No runtime consumer is wired in this phase.

**Tech Stack:** Lean 4.33.1, Lake, Python 3 standard library (`enum`, `hashlib`, `itertools`, `json`, `pathlib`, `unittest`), JSON fixtures/schemas, SHA256.

**Spec:** `docs/superpowers/specs/2026-09-12-namespace-safe-eq64-design.md`

## Global Constraints

- Mandatory order: `FORMAL SPEC -> REFERENCE ENGINE -> 720 ADVERSARIAL CANARY -> POSITIVE CONTROL -> CONTENT-ADDRESSED RECEIPT`.
- `RUNTIME_BIND = FALSE` throughout this plan.
- No active runtime imports, consumer wiring, production dependency, or engine auto-registration.
- No pointer mutation/promotion, global authority bind, or runtime admission.
- No empirical or physical validation claim.
- `STRUCTURAL REUSE MAY CROSS NAMESPACES. SEMANTIC MEANINGS MAY NOT CROSS NAMESPACES WITHOUT C1-C11 PROOF.`
- Bare `EQ64` semantic references are policy DENY.
- Criterion states are TRI-valued: PASS / HOLD / DENY. HOLD means insufficient evidence; DENY means explicit contradiction or policy conflict. Unknown is never coerced to PASS.
- No weighted score may override a failed mandatory gate.
- Maximum success claim: `PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT`.

---

## File Structure

```text
formal/namespace-safe-eq64/
├── NamespaceSafeEQ64.lean
├── NamespaceSafeEQ64Test.lean
├── lakefile.lean
├── lean-toolchain
├── README.md
├── reference/
│   ├── namespace_safe_engine.py
│   ├── permutation_canary_720.py
│   └── receipt.py
├── fixtures/
│   ├── ess_eq64_6d_kernel.json
│   ├── x_aiprbg_6gate.json
│   ├── synthetic_exact_a.json
│   └── synthetic_exact_b.json
├── schema/
│   ├── namespace.schema.json
│   ├── crosswalk_evidence.schema.json
│   └── canary_receipt.schema.json
└── tests/
    ├── test_structure.py
    ├── test_semantic_gate.py
    ├── test_720_canary.py
    └── test_positive_control.py
```

Generated full canary results and receipts are caller-supplied output files under `/tmp` during verification and are not committed.

---

### Task 1: Bootstrap the isolated Lean package and typed namespace/evidence model

**Files:**
- Create: `formal/namespace-safe-eq64/lean-toolchain`
- Create: `formal/namespace-safe-eq64/lakefile.lean`
- Create: `formal/namespace-safe-eq64/NamespaceSafeEQ64.lean`
- Create: `formal/namespace-safe-eq64/NamespaceSafeEQ64Test.lean`

**Interfaces:**
- Produces: `NamespaceId`, `Polarity`, `StructuralClass`, `Tri`, `State6`, `AxisSchema`, `PolaritySchema`, `NamespaceSpec`, `SemanticEvidence`, `CrosswalkCandidate`, `SemanticRequestAllowed`, `ExactSemanticAuthorized`.

- [ ] **Step 1: Pin the same Lean toolchain family already used by the repository**

`lean-toolchain`:

```text
leanprover/lean4:v4.33.1
```

`lakefile.lean`:

```lean
import Lake
open Lake DSL

package namespaceSafeEq64 where

@[default_target]
lean_lib NamespaceSafeEQ64
```

- [ ] **Step 2: Write the initial failing theorem/type checks**

Create `NamespaceSafeEQ64Test.lean`:

```lean
import NamespaceSafeEQ64
open NamespaceSafeEQ64

#check NamespaceId
#check Polarity
#check StructuralClass
#check Tri
#check State6
#check AxisSchema
#check SemanticEvidence
#check CrosswalkCandidate
#check ExactSemanticAuthorized
#check SemanticRequestAllowed
```

- [ ] **Step 3: Run the test and confirm RED**

```bash
cd formal/namespace-safe-eq64
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: FAIL with unknown identifiers because `NamespaceSafeEQ64.lean` is not implemented.

- [ ] **Step 4: Add the minimal typed model**

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
  c1SourceIdentity : Tri
  c2StructuralClass : Tri
  c3AxisCompleteness : Tri
  c4Polarity : Tri
  c5ConflictFree : Tri
  c6BijectionCandidate : Tri
  c7AxisEvidence : Tri
  c8OrderSemantics : Tri
  c9NoPostHocSelection : Tri
  c10GovernanceScope : Tri
  c11ClaimCeiling : Tri
  deriving Repr

structure CrosswalkCandidate where
  source : NamespaceId
  target : NamespaceId
  permutation : Equiv.Perm (Fin 6)
  evidence : SemanticEvidence


def SemanticRequestAllowed (c : CrosswalkCandidate) : Prop :=
  c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64


def ExactSemanticAuthorized (c : CrosswalkCandidate) : Prop :=
  SemanticRequestAllowed c ∧
  c.evidence.c1SourceIdentity = .pass ∧
  c.evidence.c2StructuralClass = .pass ∧
  c.evidence.c3AxisCompleteness = .pass ∧
  c.evidence.c4Polarity = .pass ∧
  c.evidence.c5ConflictFree = .pass ∧
  c.evidence.c6BijectionCandidate = .pass ∧
  c.evidence.c7AxisEvidence = .pass ∧
  c.evidence.c8OrderSemantics = .pass ∧
  c.evidence.c9NoPostHocSelection = .pass ∧
  c.evidence.c10GovernanceScope = .pass ∧
  c.evidence.c11ClaimCeiling = .pass

end NamespaceSafeEQ64
```

- [ ] **Step 5: Run the type checks and confirm GREEN**

```bash
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add formal/namespace-safe-eq64/{lean-toolchain,lakefile.lean,NamespaceSafeEQ64.lean,NamespaceSafeEQ64Test.lean}
git commit -m "feat: add namespace-safe EQ64 formal types"
```

---

### Task 2: Prove B6/Q6 structural preservation under coordinate permutations

**Files:**
- Modify: `formal/namespace-safe-eq64/NamespaceSafeEQ64.lean`
- Modify: `formal/namespace-safe-eq64/NamespaceSafeEQ64Test.lean`

**Interfaces:**
- Produces: `bMeet`, `bJoin`, `applyPerm`, `HammingOne`, `coordinate_permutation_preserves_B6_structure`, `coordinate_permutation_preserves_Q6_hamming`.

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

- [ ] **Step 2: Run and confirm RED**

```bash
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: FAIL on the new names.

- [ ] **Step 3: Add B6 operations and the coordinate permutation action**

Insert before `end NamespaceSafeEQ64`:

```lean
def bMeet (a b : State6) : State6 := fun i => a i && b i

def bJoin (a b : State6) : State6 := fun i => a i || b i

def applyPerm (p : Equiv.Perm (Fin 6)) (s : State6) : State6 :=
  fun i => s (p.symm i)

/-- Q6 adjacency expressed as Hamming distance exactly one. -/
def HammingOne (a b : State6) : Prop :=
  ∃ j : Fin 6, a j ≠ b j ∧ ∀ i : Fin 6, i ≠ j → a i = b i
```

- [ ] **Step 4: Prove meet/join preservation**

```lean
theorem coordinate_permutation_preserves_B6_structure
    (p : Equiv.Perm (Fin 6)) (a b : State6) :
    applyPerm p (bMeet a b) = bMeet (applyPerm p a) (applyPerm p b) ∧
    applyPerm p (bJoin a b) = bJoin (applyPerm p a) (applyPerm p b) := by
  constructor <;> funext i <;> rfl
```

- [ ] **Step 5: Prove Hamming-one/Q6 adjacency preservation**

```lean
theorem coordinate_permutation_preserves_Q6_hamming
    (p : Equiv.Perm (Fin 6)) (a b : State6)
    (h : HammingOne a b) :
    HammingOne (applyPerm p a) (applyPerm p b) := by
  rcases h with ⟨j, hjdiff, hjrest⟩
  refine ⟨p j, ?_, ?_⟩
  · change a (p.symm (p j)) ≠ b (p.symm (p j))
    simpa using hjdiff
  · intro i hi
    change a (p.symm i) = b (p.symm i)
    apply hjrest
    intro hEq
    apply hi
    calc
      i = p (p.symm i) := (p.apply_symm_apply i).symm
      _ = p j := congrArg p hEq
```

- [ ] **Step 6: Run Lean and scan for proof escapes**

```bash
lake env lean NamespaceSafeEQ64Test.lean
! grep -R "\bsorry\b\|\badmit\b\|\baxiom\b" -n NamespaceSafeEQ64.lean NamespaceSafeEQ64Test.lean
```

Expected: both commands exit 0; no proof escape appears.

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
- Produces: `missing_axis_evidence_blocks_exact_crosswalk`, `polarity_conflict_blocks_exact_crosswalk`, `namespace_identity_required`, `no_semantic_authorization_from_structure_alone`.

- [ ] **Step 1: Add failing theorem checks**

```lean
#check missing_axis_evidence_blocks_exact_crosswalk
#check polarity_conflict_blocks_exact_crosswalk
#check namespace_identity_required
#check no_semantic_authorization_from_structure_alone
```

- [ ] **Step 2: Run and confirm RED**

```bash
lake env lean NamespaceSafeEQ64Test.lean
```

Expected: FAIL on unknown theorem identifiers.

- [ ] **Step 3: Add the semantic safety theorems**

Insert before `end NamespaceSafeEQ64`:

```lean
theorem missing_axis_evidence_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hMissing : c.evidence.c7AxisEvidence = .hold) :
    ¬ ExactSemanticAuthorized c := by
  simp [ExactSemanticAuthorized, hMissing]


theorem polarity_conflict_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hConflict : c.evidence.c4Polarity = .deny) :
    ¬ ExactSemanticAuthorized c := by
  simp [ExactSemanticAuthorized, hConflict]


theorem namespace_identity_required
    (c : CrosswalkCandidate)
    (h : ExactSemanticAuthorized c) :
    c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64 :=
  h.1


theorem no_semantic_authorization_from_structure_alone
    (c : CrosswalkCandidate)
    (structuralIso : Prop)
    (_hStructural : structuralIso)
    (hNoAxisEvidence : c.evidence.c7AxisEvidence = .hold) :
    ¬ ExactSemanticAuthorized c :=
  missing_axis_evidence_blocks_exact_crosswalk c hNoAxisEvidence
```

- [ ] **Step 4: Add concrete HOLD, DENY, and bare-name countermodels**

Append to `NamespaceSafeEQ64Test.lean`:

```lean
def evidencePass : SemanticEvidence := {
  c1SourceIdentity := .pass, c2StructuralClass := .pass,
  c3AxisCompleteness := .pass, c4Polarity := .pass,
  c5ConflictFree := .pass, c6BijectionCandidate := .pass,
  c7AxisEvidence := .pass, c8OrderSemantics := .pass,
  c9NoPostHocSelection := .pass, c10GovernanceScope := .pass,
  c11ClaimCeiling := .pass
}

def evidenceMissingAxis : SemanticEvidence :=
  { evidencePass with c7AxisEvidence := .hold }

def evidencePolarityConflict : SemanticEvidence :=
  { evidencePass with c4Polarity := .deny }

def bareCandidate : CrosswalkCandidate := {
  source := .bareEq64,
  target := .essEq64Kernel,
  permutation := Equiv.refl (Fin 6),
  evidence := evidencePass
}

def missingAxisCandidate : CrosswalkCandidate := {
  source := .aipRbgDiagnostic,
  target := .essEq64Kernel,
  permutation := Equiv.refl (Fin 6),
  evidence := evidenceMissingAxis
}

def polarityConflictCandidate : CrosswalkCandidate := {
  source := .aipRbgDiagnostic,
  target := .essEq64Kernel,
  permutation := Equiv.refl (Fin 6),
  evidence := evidencePolarityConflict
}

example : ¬ ExactSemanticAuthorized bareCandidate := by
  intro h
  exact h.1.1 rfl

example : ¬ ExactSemanticAuthorized missingAxisCandidate :=
  missing_axis_evidence_blocks_exact_crosswalk missingAxisCandidate rfl

example : ¬ ExactSemanticAuthorized polarityConflictCandidate :=
  polarity_conflict_blocks_exact_crosswalk polarityConflictCandidate rfl
```

- [ ] **Step 5: Run the complete Lean gate**

```bash
lake build
lake env lean NamespaceSafeEQ64Test.lean
! grep -R "\bsorry\b\|\badmit\b\|\baxiom\b" -n NamespaceSafeEQ64.lean NamespaceSafeEQ64Test.lean
```

Expected: all exit 0.

- [ ] **Step 6: Commit**

```bash
git add formal/namespace-safe-eq64/NamespaceSafeEQ64*.lean
git commit -m "feat: prove namespace semantic non-inference"
```

---

### Task 4: Add canonical fixtures, TRI schemas, and the structural reference engine

**Files:**
- Create: `formal/namespace-safe-eq64/fixtures/ess_eq64_6d_kernel.json`
- Create: `formal/namespace-safe-eq64/fixtures/x_aiprbg_6gate.json`
- Create: `formal/namespace-safe-eq64/schema/namespace.schema.json`
- Create: `formal/namespace-safe-eq64/schema/crosswalk_evidence.schema.json`
- Create: `formal/namespace-safe-eq64/reference/namespace_safe_engine.py`
- Create: `formal/namespace-safe-eq64/tests/test_structure.py`

**Interfaces:**
- Produces: `Tri`, `load_namespace`, `validate_namespace`, `all_states`, `encode_state`, `decode_state`, `normalize_polarity`, `apply_permutation`, `meet`, `join`, `hamming_distance`, `check_structural_mapping`.

- [ ] **Step 1: Create the canonical real fixtures**

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

- [ ] **Step 2: Create strict namespace and evidence schemas**

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
        "C1": {"enum": ["PASS", "HOLD", "DENY"]}, "C2": {"enum": ["PASS", "HOLD", "DENY"]},
        "C3": {"enum": ["PASS", "HOLD", "DENY"]}, "C4": {"enum": ["PASS", "HOLD", "DENY"]},
        "C5": {"enum": ["PASS", "HOLD", "DENY"]}, "C6": {"enum": ["PASS", "HOLD", "DENY"]},
        "C7": {"enum": ["PASS", "HOLD", "DENY"]}, "C8": {"enum": ["PASS", "HOLD", "DENY"]},
        "C9": {"enum": ["PASS", "HOLD", "DENY"]}, "C10": {"enum": ["PASS", "HOLD", "DENY"]},
        "C11": {"enum": ["PASS", "HOLD", "DENY"]}
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
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import (
    all_states, check_structural_mapping, decode_state, encode_state,
    hamming_distance, load_namespace, normalize_polarity, validate_namespace,
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
            self.assertEqual(normalize_polarity(self.ess, normalize_polarity(self.ess, state)), state)

    def test_identity_structural_mapping(self):
        result = check_structural_mapping(tuple(range(6)))
        self.assertEqual(result, {"meet_preserved": True, "join_preserved": True, "hamming_preserved": True})

    def test_hamming_examples(self):
        self.assertEqual(hamming_distance((0,0,0,0,0,0), (1,0,0,0,0,0)), 1)
        self.assertEqual(hamming_distance((0,0,0,0,0,0), (1,1,0,0,0,0)), 2)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the structural tests and confirm RED**

```bash
cd formal/namespace-safe-eq64
python -m unittest discover -s tests -p 'test_structure.py' -v
```

Expected: FAIL because `namespace_safe_engine.py` does not exist.

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
    if len(state) != 6 or any(bit not in (0, 1) for bit in state):
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
    meet_ok = join_ok = hamming_ok = True
    for a in states:
        pa = apply_permutation(a, permutation)
        for b in states:
            pb = apply_permutation(b, permutation)
            meet_ok &= apply_permutation(meet(a, b), permutation) == meet(pa, pb)
            join_ok &= apply_permutation(join(a, b), permutation) == join(pa, pb)
            hamming_ok &= hamming_distance(a, b) == hamming_distance(pa, pb)
    return {"meet_preserved": bool(meet_ok), "join_preserved": bool(join_ok), "hamming_preserved": bool(hamming_ok)}
```

- [ ] **Step 6: Run structural tests and confirm GREEN**

```bash
python -m unittest discover -s tests -p 'test_structure.py' -v
```

Expected: all PASS.

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
- Produces: `check_semantic_crosswalk(source, target, evidence, permutation)` and `classify_mapping(source, target, evidence, permutation)`.

- [ ] **Step 1: Write failing semantic policy tests**

Create `tests/test_semantic_gate.py`:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import Tri, check_semantic_crosswalk, load_namespace

IDENTITY = tuple(range(6))
PASS11 = {f"C{i}": "PASS" for i in range(1, 12)}
HOLD11 = {f"C{i}": "HOLD" for i in range(1, 12)}
FULL_EQ = [{"source": i, "target": i, "evidence_id": f"E-{i}"} for i in range(6)]

class SemanticGateTests(unittest.TestCase):
    def setUp(self):
        self.ess = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        self.aip = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")

    def test_real_namespaces_without_semantic_evidence_hold(self):
        evidence = {"criteria": dict(HOLD11), "axis_equivalences": [], "exact_mapping": None}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)
        self.assertIn("NO_AXIS_LEVEL_EVIDENCE", result["reason_codes"])

    def test_five_of_six_axis_evidence_holds(self):
        evidence = {"criteria": dict(PASS11), "axis_equivalences": FULL_EQ[:5], "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)

    def test_polarity_conflict_denies(self):
        criteria = dict(PASS11); criteria["C4"] = "DENY"
        evidence = {"criteria": criteria, "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("POLARITY_CONFLICT", result["reason_codes"])

    def test_alias_conflict_denies(self):
        criteria = dict(PASS11); criteria["C5"] = "DENY"
        evidence = {"criteria": criteria, "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)

    def test_post_hoc_selection_denies(self):
        criteria = dict(PASS11); criteria["C9"] = "DENY"
        evidence = {"criteria": criteria, "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(self.aip, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)

    def test_bare_eq64_denies_by_policy(self):
        bare = dict(self.aip); bare["namespace_id"] = "EQ64"
        evidence = {"criteria": dict(PASS11), "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(bare, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.DENY)
        self.assertIn("DENY_POLICY_BARE_EQ64_FORBIDDEN", result["reason_codes"])

    def test_unknown_namespace_holds(self):
        unknown = dict(self.aip); unknown["namespace_id"] = "UNKNOWN_NAMESPACE"
        evidence = {"criteria": dict(PASS11), "axis_equivalences": FULL_EQ, "exact_mapping": list(IDENTITY)}
        result = check_semantic_crosswalk(unknown, self.ess, evidence, IDENTITY)
        self.assertEqual(result["status"], Tri.HOLD)
        self.assertIn("UNREGISTERED_NAMESPACE", result["reason_codes"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and confirm RED**

```bash
python -m unittest discover -s tests -p 'test_semantic_gate.py' -v
```

Expected: FAIL because `check_semantic_crosswalk` is undefined.

- [ ] **Step 3: Implement exact TRI semantics**

Append to `reference/namespace_safe_engine.py`:

```python
def _criterion_reason(key: str) -> str:
    return {
        "C4": "POLARITY_CONFLICT",
        "C5": "ALIAS_CONFLICT",
        "C9": "POST_HOC_SELECTION",
    }.get(key, f"CRITERION_DENY_{key}")


def _axis_mapping(axis_equivalences: list[dict]) -> tuple[int, ...] | None:
    if len(axis_equivalences) != 6:
        return None
    pairs = {(item.get("source"), item.get("target")) for item in axis_equivalences}
    if len(pairs) != 6:
        return None
    sources = {s for s, _ in pairs}
    targets = {t for _, t in pairs}
    if sources != set(range(6)) or targets != set(range(6)):
        return None
    by_source = dict(pairs)
    return tuple(by_source[i] for i in range(6))


def check_semantic_crosswalk(source: dict, target: dict, evidence: dict, permutation: tuple[int, ...]) -> dict:
    _validate_permutation(permutation)
    source_id = source.get("namespace_id")
    target_id = target.get("namespace_id")

    if source_id == "EQ64" or target_id == "EQ64":
        return {"status": Tri.DENY, "reason_codes": ["DENY_POLICY_BARE_EQ64_FORBIDDEN"]}
    if source_id not in REGISTERED_NAMESPACES or target_id not in REGISTERED_NAMESPACES:
        return {"status": Tri.HOLD, "reason_codes": ["UNREGISTERED_NAMESPACE"]}

    criteria = evidence.get("criteria", {})
    required = [f"C{i}" for i in range(1, 12)]
    if set(criteria) != set(required):
        return {"status": Tri.HOLD, "reason_codes": ["INCOMPLETE_C1_C11_EVIDENCE"]}
    invalid_values = [key for key in required if criteria[key] not in {"PASS", "HOLD", "DENY"}]
    if invalid_values:
        return {"status": Tri.DENY, "reason_codes": ["INVALID_CRITERION_STATE"]}
    denied = [key for key in required if criteria[key] == "DENY"]
    if denied:
        return {"status": Tri.DENY, "reason_codes": [_criterion_reason(denied[0])]}

    derived_mapping = _axis_mapping(evidence.get("axis_equivalences", []))
    if criteria["C7"] != "PASS" or derived_mapping is None:
        return {"status": Tri.HOLD, "reason_codes": ["NO_AXIS_LEVEL_EVIDENCE"]}
    if any(criteria[key] != "PASS" for key in required):
        return {"status": Tri.HOLD, "reason_codes": ["INCOMPLETE_C1_C11_EVIDENCE"]}

    exact = evidence.get("exact_mapping")
    if exact is None:
        return {"status": Tri.HOLD, "reason_codes": ["NO_PREDECLARED_EXACT_MAPPING"]}
    exact_tuple = tuple(exact)
    if derived_mapping != exact_tuple:
        return {"status": Tri.DENY, "reason_codes": ["EVIDENCE_MAPPING_CONFLICT"]}
    if exact_tuple != permutation:
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

- [ ] **Step 4: Run semantic tests and confirm GREEN**

```bash
python -m unittest discover -s tests -p 'test_semantic_gate.py' -v
```

Expected: all PASS.

- [ ] **Step 5: Run the whole Python suite so far**

```bash
python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add formal/namespace-safe-eq64/reference/namespace_safe_engine.py formal/namespace-safe-eq64/tests/test_semantic_gate.py
git commit -m "feat: add fail-closed semantic crosswalk gate"
```

---

### Task 6: Implement the exhaustive 720-permutation real negative canary

**Files:**
- Create: `formal/namespace-safe-eq64/reference/permutation_canary_720.py`
- Create: `formal/namespace-safe-eq64/tests/test_720_canary.py`

**Interfaces:**
- Produces: `run_canary(source, target, evidence) -> dict` with exact summary counts and all 720 result rows.

- [ ] **Step 1: Write the failing canary test**

Create `tests/test_720_canary.py`:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary

HOLD11 = {f"C{i}": "HOLD" for i in range(1, 12)}

class Canary720Tests(unittest.TestCase):
    def test_real_namespaces_have_zero_semantic_leakage(self):
        source = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")
        target = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        evidence = {"criteria": dict(HOLD11), "axis_equivalences": [], "exact_mapping": None}
        result = run_canary(source, target, evidence)
        self.assertEqual(result["permutation_count"], 720)
        self.assertEqual(result["structural_pass"], 720)
        self.assertEqual(result["semantic_pass"], 0)
        self.assertEqual(result["semantic_hold"], 720)
        self.assertEqual(result["semantic_deny"], 0)
        self.assertEqual(result["semantic_pass_permutations"], [])
        self.assertEqual(len(result["results"]), 720)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and confirm RED**

```bash
python -m unittest discover -s tests -p 'test_720_canary.py' -v
```

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Implement exhaustive enumeration**

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
    semantic_pass_rows = [r for r in results if r["semantic_status"] == Tri.PASS.value]
    semantic_hold = sum(r["semantic_status"] == Tri.HOLD.value for r in results)
    semantic_deny = sum(r["semantic_status"] == Tri.DENY.value for r in results)
    return {
        "permutation_count": len(results),
        "structural_pass": structural_pass,
        "semantic_pass": len(semantic_pass_rows),
        "semantic_hold": semantic_hold,
        "semantic_deny": semantic_deny,
        "semantic_pass_permutations": [r["permutation"] for r in semantic_pass_rows],
        "results": results,
    }
```

- [ ] **Step 4: Run the exhaustive negative canary**

```bash
python -m unittest discover -s tests -p 'test_720_canary.py' -v
```

Expected exact result: 720 structural PASS, 0 semantic PASS, 720 semantic HOLD, 0 DENY, no semantic-pass permutation.

- [ ] **Step 5: Commit**

```bash
git add formal/namespace-safe-eq64/reference/permutation_canary_720.py formal/namespace-safe-eq64/tests/test_720_canary.py
git commit -m "test: add 720 permutation semantic leakage canary"
```

---

### Task 7: Add the synthetic one-PASS/719-DENY selectivity control

**Files:**
- Create: `formal/namespace-safe-eq64/fixtures/synthetic_exact_a.json`
- Create: `formal/namespace-safe-eq64/fixtures/synthetic_exact_b.json`
- Create: `formal/namespace-safe-eq64/tests/test_positive_control.py`

**Interfaces:**
- Consumes: `run_canary` from Task 6.
- Produces: executable evidence that the semantic gate is selective rather than permanently HOLD.

- [ ] **Step 1: Create synthetic fixtures**

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

- [ ] **Step 2: Write the synthetic positive-control test**

Create `tests/test_positive_control.py`:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import load_namespace
from permutation_canary_720 import run_canary

PASS11 = {f"C{i}": "PASS" for i in range(1, 12)}
IDENTITY = [0,1,2,3,4,5]
FULL_EQ = [{"source": i, "target": i, "evidence_id": f"SYN-{i}"} for i in range(6)]

class PositiveControlTests(unittest.TestCase):
    def test_exactly_one_predeclared_mapping_passes(self):
        source = load_namespace(ROOT / "fixtures" / "synthetic_exact_a.json")
        target = load_namespace(ROOT / "fixtures" / "synthetic_exact_b.json")
        evidence = {"criteria": dict(PASS11), "axis_equivalences": FULL_EQ, "exact_mapping": IDENTITY}
        result = run_canary(source, target, evidence)
        self.assertEqual(result["permutation_count"], 720)
        self.assertEqual(result["structural_pass"], 720)
        self.assertEqual(result["semantic_pass"], 1)
        self.assertEqual(result["semantic_hold"], 0)
        self.assertEqual(result["semantic_deny"], 719)
        self.assertEqual(result["semantic_pass_permutations"], [IDENTITY])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the positive control**

```bash
python -m unittest discover -s tests -p 'test_positive_control.py' -v
```

Expected: exactly 1 semantic PASS and 719 DENY.

- [ ] **Step 4: Run both 720-permutation tests together**

```bash
python -m unittest tests.test_720_canary tests.test_positive_control -v
```

Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add formal/namespace-safe-eq64/fixtures/synthetic_exact_*.json formal/namespace-safe-eq64/tests/test_positive_control.py
git commit -m "test: add selective semantic positive control"
```

---

### Task 8: Add content-addressed result/receipt generation and exact independent readback

**Files:**
- Create: `formal/namespace-safe-eq64/schema/canary_receipt.schema.json`
- Create: `formal/namespace-safe-eq64/reference/receipt.py`
- Modify: `formal/namespace-safe-eq64/reference/permutation_canary_720.py`
- Modify: `formal/namespace-safe-eq64/tests/test_720_canary.py`

**Interfaces:**
- Produces: `canonical_json_bytes`, `sha256_bytes`, `hash_bundle`, `write_canonical_json`, `build_receipt`, `write_receipt`, `readback_receipt`.
- The receipt binds exact source fixture bytes, target fixture bytes, evidence bytes, engine bytes, runner bytes, receipt-builder bytes, and exact canonical result-file bytes.

- [ ] **Step 1: Define the strict receipt schema**

Create `schema/canary_receipt.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema", "source_namespace", "target_namespace", "permutation_count", "structural_pass", "semantic_pass", "semantic_hold", "semantic_deny", "unexpected_passes", "fixture_sha256", "evidence_sha256", "engine_sha256", "runner_sha256", "receipt_builder_sha256", "result_sha256", "payload_sha256", "runtime_bind"],
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
    "evidence_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "engine_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "runner_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "receipt_builder_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "result_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "payload_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "runtime_bind": {"const": false}
  }
}
```

- [ ] **Step 2: Add a failing receipt roundtrip test**

Append imports and test to `tests/test_720_canary.py`:

```python
import json
import tempfile
from receipt import build_receipt, readback_receipt, write_canonical_json, write_receipt

    def test_real_receipt_roundtrip_binds_all_inputs(self):
        source_path = ROOT / "fixtures" / "x_aiprbg_6gate.json"
        target_path = ROOT / "fixtures" / "ess_eq64_6d_kernel.json"
        source = load_namespace(source_path)
        target = load_namespace(target_path)
        evidence = {"criteria": dict(HOLD11), "axis_equivalences": [], "exact_mapping": None}
        result = run_canary(source, target, evidence)
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            evidence_path = td / "evidence.json"
            result_path = td / "result.json"
            receipt_path = td / "receipt.json"
            write_canonical_json(evidence_path, evidence)
            write_canonical_json(result_path, result)
            receipt = build_receipt(ROOT, source_path, target_path, evidence_path, result_path)
            write_receipt(receipt_path, receipt)
            reread = readback_receipt(receipt_path)
        self.assertEqual(reread, receipt)
        self.assertEqual(receipt["unexpected_passes"], [])
        self.assertFalse(receipt["runtime_bind"])
```

- [ ] **Step 3: Run and confirm RED**

```bash
python -m unittest discover -s tests -p 'test_720_canary.py' -v
```

Expected: FAIL because `receipt.py` does not exist.

- [ ] **Step 4: Implement canonical writing, hashes, strict shape validation, and readback**

Create `reference/receipt.py`:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA_NAME = "EQ64_NAMESPACE_SAFE_CANARY_RECEIPT_V1"
REQUIRED = {
    "schema", "source_namespace", "target_namespace", "permutation_count",
    "structural_pass", "semantic_pass", "semantic_hold", "semantic_deny",
    "unexpected_passes", "fixture_sha256", "evidence_sha256", "engine_sha256",
    "runner_sha256", "receipt_builder_sha256", "result_sha256", "payload_sha256",
    "runtime_bind",
}
HASH_FIELDS = {
    "fixture_sha256", "evidence_sha256", "engine_sha256", "runner_sha256",
    "receipt_builder_sha256", "result_sha256", "payload_sha256",
}


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_bundle(parts: list[bytes]) -> str:
    framed = b"".join(len(part).to_bytes(8, "big") + part for part in parts)
    return sha256_bytes(framed)


def write_canonical_json(path: Path, value) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def _validate_receipt_shape(receipt: dict) -> None:
    if set(receipt) != REQUIRED:
        raise ValueError("RECEIPT_FIELDS_MISMATCH")
    if receipt["schema"] != SCHEMA_NAME or receipt["permutation_count"] != 720:
        raise ValueError("RECEIPT_SCHEMA_OR_COUNT_INVALID")
    if receipt["runtime_bind"] is not False:
        raise ValueError("RUNTIME_BIND_MUST_REMAIN_FALSE")
    if receipt["semantic_pass"] + receipt["semantic_hold"] + receipt["semantic_deny"] != 720:
        raise ValueError("SEMANTIC_COUNT_SUM_INVALID")
    for field in HASH_FIELDS:
        value = receipt[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"INVALID_SHA256:{field}")


def build_receipt(root: Path, source_path: Path, target_path: Path, evidence_path: Path, result_path: Path) -> dict:
    engine_path = root / "reference" / "namespace_safe_engine.py"
    runner_path = root / "reference" / "permutation_canary_720.py"
    builder_path = root / "reference" / "receipt.py"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    source = json.loads(source_path.read_text(encoding="utf-8"))
    target = json.loads(target_path.read_text(encoding="utf-8"))
    payload = {
        "schema": SCHEMA_NAME,
        "source_namespace": source["namespace_id"],
        "target_namespace": target["namespace_id"],
        "permutation_count": result["permutation_count"],
        "structural_pass": result["structural_pass"],
        "semantic_pass": result["semantic_pass"],
        "semantic_hold": result["semantic_hold"],
        "semantic_deny": result["semantic_deny"],
        "unexpected_passes": result["semantic_pass_permutations"],
        "fixture_sha256": hash_bundle([source_path.read_bytes(), target_path.read_bytes()]),
        "evidence_sha256": sha256_bytes(evidence_path.read_bytes()),
        "engine_sha256": sha256_bytes(engine_path.read_bytes()),
        "runner_sha256": sha256_bytes(runner_path.read_bytes()),
        "receipt_builder_sha256": sha256_bytes(builder_path.read_bytes()),
        "result_sha256": sha256_bytes(result_path.read_bytes()),
        "runtime_bind": False,
    }
    receipt = dict(payload)
    receipt["payload_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    _validate_receipt_shape(receipt)
    return receipt


def write_receipt(path: Path, receipt: dict) -> None:
    _validate_receipt_shape(receipt)
    write_canonical_json(path, receipt)


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

- [ ] **Step 5: Run receipt test and confirm GREEN**

```bash
python -m unittest discover -s tests -p 'test_720_canary.py' -v
```

Expected: PASS.

- [ ] **Step 6: Add a CLI that writes the full canonical result before the receipt**

Append to `reference/permutation_canary_720.py`:

```python
if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    from namespace_safe_engine import load_namespace
    from receipt import build_receipt, write_canonical_json, write_receipt

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--result-out", type=Path, required=True)
    parser.add_argument("--receipt-out", type=Path, required=True)
    args = parser.parse_args()

    source = load_namespace(args.source)
    target = load_namespace(args.target)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = run_canary(source, target, evidence)
    write_canonical_json(args.result_out, result)
    receipt = build_receipt(args.root, args.source, args.target, args.evidence, args.result_out)
    write_receipt(args.receipt_out, receipt)
    print(json.dumps(receipt, sort_keys=True))
```

- [ ] **Step 7: Commit**

```bash
git add formal/namespace-safe-eq64/{schema/canary_receipt.schema.json,reference/receipt.py,reference/permutation_canary_720.py,tests/test_720_canary.py}
git commit -m "feat: add content-addressed namespace canary receipt"
```

---

### Task 9: Execute the full gate, independently rehash every bound input, and document the claim ceiling

**Files:**
- Create: `formal/namespace-safe-eq64/README.md`
- Modify implementation files only if an observed test failure proves the plan code needs correction; repeat the failing test before and after the fix.
- Do not touch runtime/application files.

**Interfaces:**
- Produces final bounded phase evidence and exact readback while preserving `RUNTIME_BIND=false`.

- [ ] **Step 1: Materialize the real no-semantic-evidence input outside the repository**

```bash
cat >/tmp/aiprbg_no_semantic_evidence.json <<'JSON'
{"axis_equivalences":[],"criteria":{"C1":"HOLD","C10":"HOLD","C11":"HOLD","C2":"HOLD","C3":"HOLD","C4":"HOLD","C5":"HOLD","C6":"HOLD","C7":"HOLD","C8":"HOLD","C9":"HOLD"},"exact_mapping":null}
JSON
```

- [ ] **Step 2: Run the full Lean proof gate**

```bash
cd formal/namespace-safe-eq64
lake build
lake env lean NamespaceSafeEQ64Test.lean
! grep -R "\bsorry\b\|\badmit\b\|\baxiom\b" -n NamespaceSafeEQ64.lean NamespaceSafeEQ64Test.lean
```

Expected: all exit 0.

- [ ] **Step 3: Run all Python tests, including both exhaustive 720 runs**

```bash
python -m unittest discover -s tests -v
```

Expected: all PASS. Real AIPRBG→ESS: 720/720 structural PASS and zero semantic PASS. Synthetic: exactly 1 semantic PASS and 719 DENY.

- [ ] **Step 4: Generate the real canonical result file and its content-addressed receipt**

```bash
python reference/permutation_canary_720.py \
  --root . \
  --source fixtures/x_aiprbg_6gate.json \
  --target fixtures/ess_eq64_6d_kernel.json \
  --evidence /tmp/aiprbg_no_semantic_evidence.json \
  --result-out /tmp/eq64_namespace_safe_real_result.json \
  --receipt-out /tmp/eq64_namespace_safe_real_receipt.json
```

Expected receipt summary:

```text
permutation_count=720
structural_pass=720
semantic_pass=0
semantic_hold=720
semantic_deny=0
unexpected_passes=[]
runtime_bind=false
```

- [ ] **Step 5: Perform independent readback without importing `receipt.py`**

Run a fresh Python process that reimplements only the framing/hash rules needed for verification:

```bash
python - <<'PY'
from pathlib import Path
import hashlib, json

root = Path('.').resolve()
receipt_path = Path('/tmp/eq64_namespace_safe_real_receipt.json')
result_path = Path('/tmp/eq64_namespace_safe_real_result.json')
evidence_path = Path('/tmp/aiprbg_no_semantic_evidence.json')
source_path = root/'fixtures/x_aiprbg_6gate.json'
target_path = root/'fixtures/ess_eq64_6d_kernel.json'
engine_path = root/'reference/namespace_safe_engine.py'
runner_path = root/'reference/permutation_canary_720.py'
builder_path = root/'reference/receipt.py'

def sha(data): return hashlib.sha256(data).hexdigest()
def bundle(parts): return sha(b''.join(len(p).to_bytes(8,'big') + p for p in parts))
def canon(v): return json.dumps(v, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode('utf-8')

raw_receipt = receipt_path.read_bytes()
r = json.loads(raw_receipt)
payload = dict(r); claimed = payload.pop('payload_sha256')
assert sha(canon(payload)) == claimed
assert r['fixture_sha256'] == bundle([source_path.read_bytes(), target_path.read_bytes()])
assert r['evidence_sha256'] == sha(evidence_path.read_bytes())
assert r['engine_sha256'] == sha(engine_path.read_bytes())
assert r['runner_sha256'] == sha(runner_path.read_bytes())
assert r['receipt_builder_sha256'] == sha(builder_path.read_bytes())
assert r['result_sha256'] == sha(result_path.read_bytes())
assert r['permutation_count'] == 720
assert r['structural_pass'] == 720
assert r['semantic_pass'] == 0
assert r['semantic_hold'] == 720
assert r['semantic_deny'] == 0
assert r['unexpected_passes'] == []
assert r['runtime_bind'] is False
print('PASS_INDEPENDENT_READBACK', len(raw_receipt), sha(raw_receipt), claimed)
PY
```

Expected: one `PASS_INDEPENDENT_READBACK` line with exact receipt byte count, receipt-file SHA256, and verified payload SHA256.

- [ ] **Step 6: Write README with exact verification commands and claim ceiling**

Create `README.md` with these substantive contents:

```markdown
# Namespace-Safe EQ64 Formal/Reference Gate

This isolated subsystem separates abstract B6/Q6 structural equivalence from semantic namespace authority.

## Mandatory verification

Run from this directory:

`lake build`

`lake env lean NamespaceSafeEQ64Test.lean`

`python -m unittest discover -s tests -v`

The real `X_AIPRBG_6GATE_DIAGNOSTIC_V1 -> ESS_EQ64_6D_KERNEL` canary must produce 720/720 structural PASS and zero semantic PASS without C1-C11 axis evidence. The synthetic control must produce exactly one semantic PASS and 719 DENY.

## Claim ceiling

A fully passing run establishes only:

`PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT`

It does not establish empirical truth, physical correctness, historical semantic equivalence, global authority, general runtime admission, or production readiness.

`RUNTIME_BIND = FALSE` in this package.
```

- [ ] **Step 7: Run final regression**

```bash
lake build
lake env lean NamespaceSafeEQ64Test.lean
python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 8: Confirm the branch contains no runtime wiring**

From repository root:

```bash
git diff --name-only main...HEAD
```

Expected: changes are limited to `formal/namespace-safe-eq64/**`, `docs/superpowers/specs/2026-09-12-namespace-safe-eq64-design.md`, and `docs/superpowers/plans/2026-09-12-namespace-safe-eq64-implementation.md`. No `app.js`, `model.js`, pointer, global-authority, or active workflow file changes.

- [ ] **Step 9: Commit the README**

```bash
git add formal/namespace-safe-eq64/README.md
git commit -m "docs: document namespace-safe EQ64 verification gate"
```

- [ ] **Step 10: Report the bounded final verdict only if every mandatory assertion above passed**

```text
LEAN_FORMAL_LAYER = PASS
REFERENCE_ENGINE = PASS
720_NEGATIVE_CANARY = 720/720
SYNTHETIC_POSITIVE = 1/720
SYNTHETIC_CONFLICT_DENY = 719/720
SEMANTIC_LEAKAGE = 0
CONTENT_ADDRESSED_RECEIPT = PASS
INDEPENDENT_READBACK = PASS
RUNTIME_BIND = FALSE
FINAL = PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT
```

If any mandatory gate fails, report `FINAL = HOLD` at the first unmet proof. Do not average or compensate around it.
