import NamespaceSafeEQ64
import HomologyGate
import AbelianHomologyGate
import NatIndexedHomologyGate
import CrossUniverseHomologyGate
import MathlibHomologicalComplexBridge
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
#check structure_preservation_with_missing_axis_evidence_does_not_authorize_semantics

/-! Lean side of the C1-C11 tri-state contract parity gate. -/
#check AnyCriterionDeny
#check AllCriteriaPass
#check criterionDecision
#check criterionDecision_eq_deny_iff
#check criterionDecision_eq_pass_iff
#check criterionDecision_eq_hold_iff
#check exactSemanticAuthorized_iff_request_allowed_and_criterionDecision_pass

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

example :
    (∀ a b : State6,
      applyPerm missingAxisCandidate.permutation (bMeet a b) =
        bMeet (applyPerm missingAxisCandidate.permutation a) (applyPerm missingAxisCandidate.permutation b) ∧
      applyPerm missingAxisCandidate.permutation (bJoin a b) =
        bJoin (applyPerm missingAxisCandidate.permutation a) (applyPerm missingAxisCandidate.permutation b)) ∧
    (∀ a b : State6, HammingOne a b →
      HammingOne (applyPerm missingAxisCandidate.permutation a) (applyPerm missingAxisCandidate.permutation b)) ∧
    ¬ ExactSemanticAuthorized missingAxisCandidate :=
  structure_preservation_with_missing_axis_evidence_does_not_authorize_semantics
    missingAxisCandidate rfl

example : criterionDecision evidencePass = .pass := by
  exact (criterionDecision_eq_pass_iff evidencePass).2 ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩

example : criterionDecision evidenceMissingAxis = .hold := by
  apply (criterionDecision_eq_hold_iff evidenceMissingAxis).2
  constructor
  · intro h
    rcases h with h | h | h | h | h | h | h | h | h | h | h <;> simp [evidenceMissingAxis, evidencePass] at h
  · intro hPass
    exact Tri.noConfusion (hPass.2.2.2.2.2.2.1)

example : criterionDecision evidencePolarityConflict = .deny := by
  apply (criterionDecision_eq_deny_iff evidencePolarityConflict).2
  exact Or.inr (Or.inr (Or.inr (Or.inl rfl)))

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

/-! General abelian chain-complex homology lift gate. -/
#check HomologyGate.AbelianChainData
#check HomologyGate.abelian_boundary_sq_zero
#check HomologyGate.abelian_image_subset_kernel
#check HomologyGate.abelian_boundary_shift_preserves_cycle
#check HomologyGate.abelianHomologySetoid
#check HomologyGate.AbelianHomologyQuotient
#check HomologyGate.abelian_quotient_eq_of_homologous
#check HomologyGate.intPair_boundary_sq_zero
#check HomologyGate.intPair_kernel_subset_image
#check HomologyGate.abelian_local_conditions_do_not_force_global_nontriviality

/-! N-indexed abelian chain-complex and degreewise homology gate. -/
#check HomologyGate.NatIndexedChainData
#check HomologyGate.nat_boundary_sq_zero
#check HomologyGate.nat_image_subset_kernel
#check HomologyGate.nat_boundary_shift_preserves_cycle
#check HomologyGate.natHomologySetoid
#check HomologyGate.NatHomologyQuotient
#check HomologyGate.nat_quotient_eq_of_homologous
#check HomologyGate.threeTermNatChain
#check HomologyGate.threeTerm_boundary_one_eq
#check HomologyGate.threeTerm_boundary_two_eq
#check HomologyGate.threeTerm_degree_one_kernel_iff
#check HomologyGate.threeTerm_degree_one_image_iff
#check HomologyGate.threeTermDegreeOneCycleEquiv
#check HomologyGate.threeTerm_degree_one_homologous_iff
#check HomologyGate.threeTermDegreeOneHomologyEquiv

/-! Cross-universe ULift compatibility gate for the original three-term model. -/
#check HomologyGate.ULiftedThreeTermCarrier
#check HomologyGate.uliftedThreeTermNatChain
#check HomologyGate.uliftedThreeTerm_boundary_one_down_eq
#check HomologyGate.uliftedThreeTerm_boundary_two_down_eq
#check HomologyGate.uliftedThreeTerm_degree_one_kernel_iff
#check HomologyGate.uliftedThreeTerm_degree_one_image_iff
#check HomologyGate.uliftedThreeTermDegreeOneCycleEquiv
#check HomologyGate.uliftedThreeTerm_degree_one_homologous_iff
#check HomologyGate.uliftedThreeTermDegreeOneHomologyEquiv

/-! Mathlib HomologicalComplex interoperability and homology bridge: RED contract. -/
#check HomologyGate.mathlibChainComplex
#check HomologyGate.mathlib_chain_X_coe
#check HomologyGate.mathlib_chain_d_succ_apply
#check HomologyGate.mathlib_chain_d_nonrel_eq_zero
#check HomologyGate.mathlib_chain_d_comp_d_apply
#check HomologyGate.mathlib_degree_cycle_iff
#check HomologyGate.mathlib_degree_boundary_iff
#check HomologyGate.mathlibDegreeHomologyMap
#check HomologyGate.mathlibDegreeHomologyMap_surjective
#check HomologyGate.mathlibDegreeHomologyMap_eq_iff
#check HomologyGate.mathlibDegreeHomologyEquiv

/-! LEAN_EQ64_CARDINALITY_AND_NONCOMPENSATING_GATE_V1: RED contract. -/
#check eq64_state_cardinality
#check AllGatesPass
#check false_gate_blocks_all_pass

example : Fintype.card State6 = 64 := eq64_state_cardinality

example (s : State6) (i : Fin 6) (hFalse : s i = false) :
    ¬ AllGatesPass s :=
  false_gate_blocks_all_pass s i hFalse
