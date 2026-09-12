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
  permutation : Equiv (Fin 6) (Fin 6)
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
