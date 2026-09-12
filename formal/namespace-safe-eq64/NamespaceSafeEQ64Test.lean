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
#check exact_authorization_requires_mapping_match
#check mapping_mismatch_blocks_exact_crosswalk
#check exact_authorization_unique_for_predeclared_mapping

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
  exactMapping := identityPermutation6
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

example (c : CrosswalkCandidate) (h : ExactSemanticAuthorized c) :
    SamePermutation c.permutation c.evidence.exactMapping :=
  exact_authorization_requires_mapping_match c h
