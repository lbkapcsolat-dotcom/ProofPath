import NamespaceSafeEQ64
import HomologyGate
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

#check bMeet
#check bJoin
#check applyPerm
#check HammingOne
#check coordinate_permutation_preserves_B6_structure
#check coordinate_permutation_preserves_Q6_hamming

#check missing_axis_evidence_blocks_exact_crosswalk
#check polarity_conflict_blocks_exact_crosswalk
#check namespace_identity_required
#check no_semantic_authorization_from_structure_alone

def identityPermutation6 : Permutation6 := {
  toFun := fun i => i
  invFun := fun i => i
  leftInv := by intro i; rfl
  rightInv := by intro i; rfl
}

def evidencePass : SemanticEvidence := {
  c1SourceIdentity := .pass
  c2StructuralClass := .pass
  c3AxisCompleteness := .pass
  c4Polarity := .pass
  c5ConflictFree := .pass
  c6BijectionCandidate := .pass
  c7AxisEvidence := .pass
  c8OrderSemantics := .pass
  c9NoPostHocSelection := .pass
  c10GovernanceScope := .pass
  c11ClaimCeiling := .pass
}

def evidenceMissingAxis : SemanticEvidence :=
  { evidencePass with c7AxisEvidence := .hold }

def evidencePolarityConflict : SemanticEvidence :=
  { evidencePass with c4Polarity := .deny }

def bareCandidate : CrosswalkCandidate := {
  source := .bareEq64
  target := .essEq64Kernel
  permutation := identityPermutation6
  evidence := evidencePass
}

def missingAxisCandidate : CrosswalkCandidate := {
  source := .aipRbgDiagnostic
  target := .essEq64Kernel
  permutation := identityPermutation6
  evidence := evidenceMissingAxis
}

def polarityConflictCandidate : CrosswalkCandidate := {
  source := .aipRbgDiagnostic
  target := .essEq64Kernel
  permutation := identityPermutation6
  evidence := evidencePolarityConflict
}

example : ¬ ExactSemanticAuthorized bareCandidate := by
  intro h
  exact h.1.1 rfl

example : ¬ ExactSemanticAuthorized missingAxisCandidate :=
  missing_axis_evidence_blocks_exact_crosswalk missingAxisCandidate rfl

example : ¬ ExactSemanticAuthorized polarityConflictCandidate :=
  polarity_conflict_blocks_exact_crosswalk polarityConflictCandidate rfl

/-! Machine-checkable characteristic-two homology gate. -/
#check HomologyGate.boundary_sq_zero
#check HomologyGate.image_subset_kernel_of_sq_zero
#check HomologyGate.boundary_shift_preserves_cycle
#check HomologyGate.homologySetoid
#check HomologyGate.HomologyQuotient
#check HomologyGate.quotient_eq_of_homologous
#check HomologyGate.tiny_boundary_sq_zero
#check HomologyGate.tiny_kernel_subset_image
#check HomologyGate.local_conditions_do_not_force_global_nontriviality

/-!
General abelian lift gate. These contracts intentionally precede implementation
so CI must first fail on missing generic theorems.
-/
#check HomologyGate.AbelianChainData
#check HomologyGate.abelian_boundary_sq_zero
#check HomologyGate.abelian_image_subset_kernel
#check HomologyGate.abelian_boundary_shift_preserves_cycle
#check HomologyGate.abelianHomologySetoid
#check HomologyGate.AbelianHomologyQuotient
#check HomologyGate.intPair_boundary_sq_zero
#check HomologyGate.intPair_kernel_subset_image
#check HomologyGate.abelian_local_conditions_do_not_force_global_nontriviality
