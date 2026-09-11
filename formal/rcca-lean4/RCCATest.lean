import RCCA

open RCCA

#check rcca_refinement_nonweakening
#check restore_requires_recoverable
#check restore_requires_recovery_authority
#check runtime_recovery_authority_separation
#check recovery_witness_bundle_mismatch_invalid
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
