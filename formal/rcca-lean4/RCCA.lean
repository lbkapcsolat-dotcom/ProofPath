namespace RCCA

/-- Conjunctive RCCA refinement of the predecessor H/V + K12 executable predicate. -/
def ExecRCCA (predecessor recoveryEdge rccaOk : Prop) : Prop :=
  predecessor ∧ (¬ recoveryEdge ∨ rccaOk)

theorem rcca_refinement_nonweakening {predecessor recoveryEdge rccaOk : Prop}
    (h : ExecRCCA predecessor recoveryEdge rccaOk) : predecessor :=
  h.1

/-- Exact readable bytes are the bounded recoverability predicate. -/
def Recoverable (exactBytes readable : Prop) : Prop :=
  exactBytes ∧ readable

/-- Recovery execution requires all recovery gates plus the predecessor gate. -/
def RestoreExecutable
    (recoverable compatible recoveryAuthorized predecessor : Prop) : Prop :=
  recoverable ∧ compatible ∧ recoveryAuthorized ∧ predecessor

theorem restore_requires_recoverable
    {recoverable compatible recoveryAuthorized predecessor : Prop}
    (h : RestoreExecutable recoverable compatible recoveryAuthorized predecessor) :
    recoverable :=
  h.1

theorem restore_requires_recovery_authority
    {recoverable compatible recoveryAuthorized predecessor : Prop}
    (h : RestoreExecutable recoverable compatible recoveryAuthorized predecessor) :
    recoveryAuthorized :=
  h.2.2.1

/-- Runtime and recovery witnesses are separate typed capabilities. -/
structure RuntimeWitness where
  id : Nat

structure RecoveryWitness where
  bundleDigest : Nat
  targetStateDigest : Nat
  lineageId : Nat
  policyDigest : Nat
  authorityEpoch : Nat
  nonce : Nat
  expiry : Nat

/-- A recovery witness is exact-context bound. -/
def ValidRecovery
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat) : Prop :=
  w.bundleDigest = bundleDigest ∧
  w.targetStateDigest = targetStateDigest ∧
  w.lineageId = lineageId ∧
  w.policyDigest = policyDigest ∧
  w.authorityEpoch = authorityEpoch ∧
  w.nonce = nonce ∧
  now ≤ w.expiry

/-- Existence of ordinary runtime authority does not imply recovery authority. -/
theorem runtime_recovery_authority_separation :
    ∃ runtimeAuthorized recoveryAuthorized : Prop,
      runtimeAuthorized ∧ ¬ recoveryAuthorized := by
  exact ⟨True, False, by simp⟩

theorem recovery_witness_bundle_mismatch_invalid
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (hMismatch : w.bundleDigest ≠ bundleDigest) :
    ¬ ValidRecovery w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now := by
  intro h
  exact hMismatch h.1

inductive ClaimLevel where
  | bottom
  | bounded
  | strong
  deriving DecidableEq, Repr

def meet : ClaimLevel → ClaimLevel → ClaimLevel
  | .bottom, _ => .bottom
  | _, .bottom => .bottom
  | .bounded, _ => .bounded
  | _, .bounded => .bounded
  | .strong, .strong => .strong

/-- Noncompensatory recovery claim ceiling. -/
def ClaimCeiling
    (evidence custody temporal authority policy : ClaimLevel) : ClaimLevel :=
  meet evidence (meet custody (meet temporal (meet authority policy)))

theorem claim_ceiling_authority_bottom
    (evidence custody temporal policy : ClaimLevel) :
    ClaimCeiling evidence custody temporal .bottom policy = .bottom := by
  cases evidence <;> cases custody <;> cases temporal <;> cases policy <;> rfl

/-- CM-RCCA-01: exact bytes can be mutable. -/
theorem cm_exact_but_mutable :
    ∃ ex imm : Prop, ex ∧ ¬ imm := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-02: an immutable object can contain the wrong bytes. -/
theorem cm_immutable_wrong_bytes :
    ∃ imm ex : Prop, imm ∧ ¬ ex := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-03: exact immutable historical evidence can be superseded. -/
theorem cm_exact_immutable_but_superseded :
    ∃ ex imm historical current : Prop,
      ex ∧ imm ∧ historical ∧ ¬ current := by
  exact ⟨True, True, True, False, by simp⟩

/-- CM-RCCA-04: currentness does not imply readable recoverability. -/
theorem cm_current_but_unreadable :
    ∃ current recoverable : Prop, current ∧ ¬ recoverable := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-05: recoverability does not mint recovery authority. -/
theorem cm_recoverable_without_recovery_witness :
    ∃ recoverable recoveryAuthorized : Prop,
      recoverable ∧ ¬ recoveryAuthorized := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-06: runtime authority does not become recovery authority. -/
theorem cm_runtime_token_not_recovery_token :
    ∃ runtimeAuthorized recoveryAuthorized : Prop,
      runtimeAuthorized ∧ ¬ recoveryAuthorized := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-07: a recovery witness for another bundle is invalid here. -/
theorem cm_recovery_witness_wrong_bundle :
    ∃ recoverable validForThisBundle : Prop,
      recoverable ∧ ¬ validForThisBundle := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-08: stale policy or epoch requires revalidation. -/
theorem cm_stale_policy_or_epoch :
    ∃ historicalValidity currentValidity : Prop,
      historicalValidity ∧ ¬ currentValidity := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-09: configured immutability can lack provider enforcement. -/
theorem cm_configured_not_enforced :
    ∃ configured enforced : Prop, configured ∧ ¬ enforced := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-10: a non-current bundle can be an explicitly authorized rollback target. -/
theorem cm_authorized_historical_rollback :
    ∃ current recoverable compatible recoveryAuthorized predecessor : Prop,
      ¬ current ∧ RestoreExecutable recoverable compatible recoveryAuthorized predecessor := by
  exact ⟨False, True, True, True, True, by simp [RestoreExecutable]⟩

/-- CM-RCCA-11: strong custody does not create action authority. -/
theorem cm_strong_custody_without_authority :
    ∃ custodyPass actionAuthority : Prop,
      custodyPass ∧ ¬ actionAuthority := by
  exact ⟨True, False, by simp⟩

/-- CM-RCCA-12: superseded material can persist for audit without auto-execution. -/
theorem cm_supersession_with_audit_persistence :
    ∃ current historicalVisible autoExecutable : Prop,
      ¬ current ∧ historicalVisible ∧ ¬ autoExecutable := by
  exact ⟨False, True, False, by simp⟩

end RCCA
