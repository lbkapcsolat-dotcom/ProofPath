import Std
import Mathlib.Data.Fintype.BigOperators

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

/-- All six EQ64 gates are true. This is the noncompensating PASS predicate. -/
def AllGatesPass (s : State6) : Prop :=
  ∀ i, s i = true

/-- The six Boolean gates form exactly 64 states. -/
theorem eq64_state_cardinality : Fintype.card State6 = 64 := by
  change Fintype.card (Fin 6 → Bool) = 64
  rw [Fintype.card_fun, Fintype.card_bool, Fintype.card_fin]
  decide

/-- Any single false gate blocks PASS, regardless of the other five gates. -/
theorem false_gate_blocks_all_pass
    (s : State6) (i : Fin 6) (hFalse : s i = false) :
    ¬ AllGatesPass s := by
  intro hAll
  have hTrue : s i = true := hAll i
  simp [hFalse] at hTrue

structure Permutation6 where
  toFun : Fin 6 → Fin 6
  invFun : Fin 6 → Fin 6
  leftInv : ∀ i, invFun (toFun i) = i
  rightInv : ∀ i, toFun (invFun i) = i

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
  permutation : Permutation6
  evidence : SemanticEvidence


def SemanticRequestAllowed (c : CrosswalkCandidate) : Prop :=
  c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64


def AllCriteriaPass (e : SemanticEvidence) : Prop :=
  e.c1SourceIdentity = .pass ∧
  e.c2StructuralClass = .pass ∧
  e.c3AxisCompleteness = .pass ∧
  e.c4Polarity = .pass ∧
  e.c5ConflictFree = .pass ∧
  e.c6BijectionCandidate = .pass ∧
  e.c7AxisEvidence = .pass ∧
  e.c8OrderSemantics = .pass ∧
  e.c9NoPostHocSelection = .pass ∧
  e.c10GovernanceScope = .pass ∧
  e.c11ClaimCeiling = .pass


def AnyCriterionDeny (e : SemanticEvidence) : Prop :=
  e.c1SourceIdentity = .deny ∨
  e.c2StructuralClass = .deny ∨
  e.c3AxisCompleteness = .deny ∨
  e.c4Polarity = .deny ∨
  e.c5ConflictFree = .deny ∨
  e.c6BijectionCandidate = .deny ∨
  e.c7AxisEvidence = .deny ∨
  e.c8OrderSemantics = .deny ∨
  e.c9NoPostHocSelection = .deny ∨
  e.c10GovernanceScope = .deny ∨
  e.c11ClaimCeiling = .deny

instance (e : SemanticEvidence) : Decidable (AllCriteriaPass e) := by
  unfold AllCriteriaPass
  infer_instance

instance (e : SemanticEvidence) : Decidable (AnyCriterionDeny e) := by
  unfold AnyCriterionDeny
  infer_instance

/-- Shared tri-state criterion contract: DENY dominates, all-PASS passes, otherwise HOLD. -/
def criterionDecision (e : SemanticEvidence) : Tri :=
  if AnyCriterionDeny e then .deny
  else if AllCriteriaPass e then .pass
  else .hold


def ExactSemanticAuthorized (c : CrosswalkCandidate) : Prop :=
  SemanticRequestAllowed c ∧ AllCriteriaPass c.evidence


theorem allCriteriaPass_excludes_deny
    (e : SemanticEvidence) (hPass : AllCriteriaPass e) :
    ¬ AnyCriterionDeny e := by
  rcases hPass with ⟨h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11⟩
  simp [AnyCriterionDeny, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11]


theorem criterionDecision_eq_deny_iff (e : SemanticEvidence) :
    criterionDecision e = .deny ↔ AnyCriterionDeny e := by
  constructor
  · intro h
    by_cases hDeny : AnyCriterionDeny e
    · exact hDeny
    · by_cases hPass : AllCriteriaPass e <;>
        simp [criterionDecision, hDeny, hPass] at h
  · intro hDeny
    simp [criterionDecision, hDeny]


theorem criterionDecision_eq_pass_iff (e : SemanticEvidence) :
    criterionDecision e = .pass ↔ AllCriteriaPass e := by
  constructor
  · intro h
    by_cases hDeny : AnyCriterionDeny e
    · simp [criterionDecision, hDeny] at h
    · by_cases hPass : AllCriteriaPass e
      · exact hPass
      · simp [criterionDecision, hDeny, hPass] at h
  · intro hPass
    have hDeny : ¬ AnyCriterionDeny e := allCriteriaPass_excludes_deny e hPass
    simp [criterionDecision, hDeny, hPass]


theorem criterionDecision_eq_hold_iff (e : SemanticEvidence) :
    criterionDecision e = .hold ↔ ¬ AnyCriterionDeny e ∧ ¬ AllCriteriaPass e := by
  constructor
  · intro h
    constructor
    · intro hDeny
      simp [criterionDecision, hDeny] at h
    · intro hPass
      have hDeny : ¬ AnyCriterionDeny e := allCriteriaPass_excludes_deny e hPass
      simp [criterionDecision, hDeny, hPass] at h
  · rintro ⟨hDeny, hPass⟩
    simp [criterionDecision, hDeny, hPass]


theorem exactSemanticAuthorized_iff_request_allowed_and_criterionDecision_pass
    (c : CrosswalkCandidate) :
    ExactSemanticAuthorized c ↔
      SemanticRequestAllowed c ∧ criterionDecision c.evidence = .pass := by
  rw [criterionDecision_eq_pass_iff]
  rfl


def bMeet (a b : State6) : State6 := fun i => a i && b i


def bJoin (a b : State6) : State6 := fun i => a i || b i


def applyPerm (p : Permutation6) (s : State6) : State6 :=
  fun i => s (p.invFun i)

/-- Q6 adjacency expressed as differing at exactly one coordinate. -/
def HammingOne (a b : State6) : Prop :=
  ∃ j : Fin 6, a j ≠ b j ∧ ∀ i : Fin 6, i ≠ j → a i = b i


theorem coordinate_permutation_preserves_B6_structure
    (p : Permutation6) (a b : State6) :
    applyPerm p (bMeet a b) = bMeet (applyPerm p a) (applyPerm p b) ∧
    applyPerm p (bJoin a b) = bJoin (applyPerm p a) (applyPerm p b) := by
  constructor <;> funext i <;> rfl


theorem coordinate_permutation_preserves_Q6_hamming
    (p : Permutation6) (a b : State6)
    (h : HammingOne a b) :
    HammingOne (applyPerm p a) (applyPerm p b) := by
  rcases h with ⟨j, hjdiff, hjrest⟩
  refine ⟨p.toFun j, ?_, ?_⟩
  · change a (p.invFun (p.toFun j)) ≠ b (p.invFun (p.toFun j))
    rw [p.leftInv j]
    exact hjdiff
  · intro i hi
    change a (p.invFun i) = b (p.invFun i)
    apply hjrest
    intro hEq
    apply hi
    calc
      i = p.toFun (p.invFun i) := (p.rightInv i).symm
      _ = p.toFun j := congrArg p.toFun hEq


theorem missing_axis_evidence_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hMissing : c.evidence.c7AxisEvidence = .hold) :
    ¬ ExactSemanticAuthorized c := by
  simp [ExactSemanticAuthorized, AllCriteriaPass, hMissing]


theorem polarity_conflict_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hConflict : c.evidence.c4Polarity = .deny) :
    ¬ ExactSemanticAuthorized c := by
  simp [ExactSemanticAuthorized, AllCriteriaPass, hConflict]


theorem namespace_identity_required
    (c : CrosswalkCandidate)
    (h : ExactSemanticAuthorized c) :
    c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64 :=
  h.1

/-- Structural B6/Q6 preservation plus missing axis semantics proves only structural
    compatibility; it does not authorize an exact semantic crosswalk. -/
theorem structure_preservation_with_missing_axis_evidence_does_not_authorize_semantics
    (c : CrosswalkCandidate)
    (hMissing : c.evidence.c7AxisEvidence = .hold) :
    (∀ a b : State6,
      applyPerm c.permutation (bMeet a b) =
        bMeet (applyPerm c.permutation a) (applyPerm c.permutation b) ∧
      applyPerm c.permutation (bJoin a b) =
        bJoin (applyPerm c.permutation a) (applyPerm c.permutation b)) ∧
    (∀ a b : State6, HammingOne a b →
      HammingOne (applyPerm c.permutation a) (applyPerm c.permutation b)) ∧
    ¬ ExactSemanticAuthorized c := by
  constructor
  · intro a b
    exact coordinate_permutation_preserves_B6_structure c.permutation a b
  · constructor
    · intro a b h
      exact coordinate_permutation_preserves_Q6_hamming c.permutation a b h
    · exact missing_axis_evidence_blocks_exact_crosswalk c hMissing

end NamespaceSafeEQ64
