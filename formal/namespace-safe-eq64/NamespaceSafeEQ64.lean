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

structure Permutation6 where
  toFun : Fin 6 → Fin 6
  invFun : Fin 6 → Fin 6
  leftInv : ∀ i, invFun (toFun i) = i
  rightInv : ∀ i, toFun (invFun i) = i


def SamePermutation (p q : Permutation6) : Prop :=
  ∀ i, p.toFun i = q.toFun i

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
  exactMapping : Permutation6

structure CrosswalkCandidate where
  source : NamespaceId
  target : NamespaceId
  permutation : Permutation6
  evidence : SemanticEvidence


def SemanticRequestAllowed (c : CrosswalkCandidate) : Prop :=
  c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64


def SemanticEvidencePass (e : SemanticEvidence) : Prop :=
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


def ExactSemanticAuthorized (c : CrosswalkCandidate) : Prop :=
  SemanticRequestAllowed c ∧
  SemanticEvidencePass c.evidence ∧
  SamePermutation c.permutation c.evidence.exactMapping


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
  simp [ExactSemanticAuthorized, SemanticEvidencePass, hMissing]


theorem polarity_conflict_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (hConflict : c.evidence.c4Polarity = .deny) :
    ¬ ExactSemanticAuthorized c := by
  simp [ExactSemanticAuthorized, SemanticEvidencePass, hConflict]


theorem namespace_identity_required
    (c : CrosswalkCandidate)
    (h : ExactSemanticAuthorized c) :
    c.source ≠ .bareEq64 ∧ c.target ≠ .bareEq64 :=
  h.1


theorem exact_authorization_requires_mapping_match
    (c : CrosswalkCandidate)
    (h : ExactSemanticAuthorized c) :
    SamePermutation c.permutation c.evidence.exactMapping :=
  h.2.2


theorem mapping_mismatch_blocks_exact_crosswalk
    (c : CrosswalkCandidate)
    (i : Fin 6)
    (hMismatch : c.permutation.toFun i ≠ c.evidence.exactMapping.toFun i) :
    ¬ ExactSemanticAuthorized c := by
  intro h
  exact hMismatch ((exact_authorization_requires_mapping_match c h) i)


theorem no_semantic_authorization_from_structure_alone
    (c : CrosswalkCandidate)
    (structuralIso : Prop)
    (_hStructural : structuralIso)
    (hNoAxisEvidence : c.evidence.c7AxisEvidence = .hold) :
    ¬ ExactSemanticAuthorized c :=
  missing_axis_evidence_blocks_exact_crosswalk c hNoAxisEvidence

end NamespaceSafeEQ64
