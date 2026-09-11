import RCCA

open RCCA

#check rcca_refinement_nonweakening
#check restore_requires_recoverable
#check restore_requires_recovery_authority
#check runtime_recovery_authority_separation
#check recovery_witness_bundle_mismatch_invalid
#check recovery_witness_consumed_invalid
#check recovery_witness_revoked_invalid
#check recovery_witness_replay_invalid
#check recovery_witness_expired_invalid
#check recovery_witness_wrong_policy_invalid
#check recovery_witness_wrong_epoch_invalid
#check superseded_bundle_not_current
#check configured_immutability_not_enforcement
#check immutable_requires_provider_enforcement
#check claim_ceiling_authority_bottom
#check cm_exact_but_mutable
#check cm_immutable_wrong_bytes
#check cm_exact_immutable_but_superseded
#check cm_current_but_unreadable
#check cm_recoverable_without_recovery_witness
#check cm_runtime_token_not_recovery_token
#check cm_recovery_witness_wrong_bundle
#check cm_stale_policy_or_epoch
#check cm_configured_not_enforced
#check cm_authorized_historical_rollback
#check cm_strong_custody_without_authority
#check cm_supersession_with_audit_persistence

example (predecessor recoveryEdge rccaOk : Prop)
    (h : ExecRCCA predecessor recoveryEdge rccaOk) : predecessor :=
  rcca_refinement_nonweakening h

example :
    ClaimCeiling .strong .strong .strong .bottom .strong = .bottom :=
  claim_ceiling_authority_bottom .strong .strong .strong .strong

/-- Concrete typed model: exactness and immutability remain separate dimensions. -/
def testSnapshot1 : Snapshot := { lineageId := 1, stateDigest := 101 }
def testSnapshot2 : Snapshot := { lineageId := 1, stateDigest := 102 }
def testBundle : Bundle := { byteDigest := 55, snapshot := testSnapshot1 }
def testMutableReplica : Replica := {
  byteDigest := 55
  readable := true
  immutable := false
  configuredImmutable := true
  enforcedImmutable := false
}

def testEnforcedReplica : Replica := {
  byteDigest := 55
  readable := true
  immutable := true
  configuredImmutable := true
  enforcedImmutable := true
}

example : Exact testBundle testMutableReplica := by
  rfl

example : ¬ Immutable testMutableReplica := by
  simp [Immutable, testMutableReplica]

example : ConfiguredImmutable testMutableReplica := by
  rfl

example : ¬ ProviderEnforcedImmutable testMutableReplica := by
  simp [ProviderEnforcedImmutable, testMutableReplica]

example : Immutable testEnforcedReplica := by
  simp [Immutable, ProviderEnforcedImmutable, testEnforcedReplica]

example (r : Replica) (h : Immutable r) : ProviderEnforcedImmutable r :=
  immutable_requires_provider_enforcement r h

example : Current testBundle testSnapshot1 := by
  rfl

example : ¬ Current testBundle testSnapshot2 := by
  exact superseded_bundle_not_current testBundle testSnapshot1 testSnapshot2 rfl (by decide)
