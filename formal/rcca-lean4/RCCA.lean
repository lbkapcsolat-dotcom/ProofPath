namespace RCCA

set_option autoImplicit false

/-- Conjunctive RCCA refinement of the predecessor H/V + K12 executable predicate. -/
def ExecRCCA (predecessor recoveryEdge rccaOk : Prop) : Prop :=
  predecessor ∧ (¬ recoveryEdge ∨ rccaOk)

theorem rcca_refinement_nonweakening {predecessor recoveryEdge rccaOk : Prop}
    (h : ExecRCCA predecessor recoveryEdge rccaOk) : predecessor :=
  h.1

/-- Logical authority-state snapshot used by currentness reasoning. -/
structure Snapshot where
  lineageId : Nat
  stateDigest : Nat
  deriving DecidableEq, Repr

/-- Recovery bundle identity. The byte digest and represented snapshot remain separate fields. -/
structure Bundle where
  byteDigest : Nat
  snapshot : Snapshot
  deriving DecidableEq, Repr

/-- Provider replica/storage evidence. Configuration and observed enforcement are separate. -/
structure Replica where
  byteDigest : Nat
  readable : Bool
  immutable : Bool
  configuredImmutable : Bool
  enforcedImmutable : Bool
  deriving DecidableEq, Repr

/-- Exactness is byte identity, not metadata identity. -/
def Exact (b : Bundle) (r : Replica) : Prop :=
  r.byteDigest = b.byteDigest

def Readable (r : Replica) : Prop :=
  r.readable = true

def ConfiguredImmutable (r : Replica) : Prop :=
  r.configuredImmutable = true

/-- Provider-native observed enforcement. -/
def ProviderEnforcedImmutable (r : Replica) : Prop :=
  r.enforcedImmutable = true

/--
Trusted immutability is deliberately stronger than configuration or a local bit:
it requires both the declared immutable state and observed provider enforcement.
-/
def Immutable (r : Replica) : Prop :=
  r.immutable = true ∧ ProviderEnforcedImmutable r

theorem immutable_requires_provider_enforcement
    (r : Replica) (h : Immutable r) : ProviderEnforcedImmutable r :=
  h.2

/-- Exact readable bytes are the bounded recoverability predicate. -/
def Recoverable (b : Bundle) (r : Replica) : Prop :=
  Exact b r ∧ Readable r

/-- Currentness is explicit equality with the authenticated lineage snapshot supplied at decision time. -/
def Current (b : Bundle) (authenticatedCurrent : Snapshot) : Prop :=
  b.snapshot = authenticatedCurrent

/-- A prior snapshot can remain historically valid after a distinct successor becomes current. -/
def HistoricalValid
    (b : Bundle) (priorCurrent authenticatedCurrent : Snapshot) (integrity : Bool) : Prop :=
  Current b priorCurrent ∧ priorCurrent ≠ authenticatedCurrent ∧ integrity = true

theorem superseded_bundle_not_current
    (b : Bundle) (priorCurrent authenticatedCurrent : Snapshot)
    (hPrior : Current b priorCurrent)
    (hDistinct : priorCurrent ≠ authenticatedCurrent) :
    ¬ Current b authenticatedCurrent := by
  intro hCurrent
  apply hDistinct
  calc
    priorCurrent = b.snapshot := hPrior.symm
    _ = authenticatedCurrent := hCurrent

/-- A configured immutability bit does not establish provider enforcement. -/
theorem configured_immutability_not_enforcement :
    ∃ r : Replica, ConfiguredImmutable r ∧ ¬ ProviderEnforcedImmutable r := by
  let r : Replica := {
    byteDigest := 1
    readable := true
    immutable := false
    configuredImmutable := true
    enforcedImmutable := false
  }
  refine ⟨r, ?_, ?_⟩
  · rfl
  · simp [ProviderEnforcedImmutable, r]

/-- Runtime and recovery witnesses are distinct typed capabilities. -/
structure RuntimeWitness where
  id : Nat
  deriving DecidableEq, Repr

structure RecoveryWitness where
  bundleDigest : Nat
  targetStateDigest : Nat
  lineageId : Nat
  policyDigest : Nat
  authorityEpoch : Nat
  nonce : Nat
  expiry : Nat
  consumed : Bool
  revoked : Bool
  deriving DecidableEq, Repr

def RuntimeAuthorized (authorized : RuntimeWitness → Prop) (w : RuntimeWitness) : Prop :=
  authorized w

/--
A valid recovery witness is both governance-authorized and exact-context bound.
The external `authorized` relation models the governed W_R authority store; merely
constructing a RecoveryWitness value does not create authority.
-/
structure ValidRecovery
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop) : Prop where
  authorized_ok : authorized w
  bundle_ok : w.bundleDigest = bundleDigest
  target_ok : w.targetStateDigest = targetStateDigest
  lineage_ok : w.lineageId = lineageId
  policy_ok : w.policyDigest = policyDigest
  epoch_ok : w.authorityEpoch = authorityEpoch
  nonce_ok : w.nonce = nonce
  not_consumed : w.consumed = false
  not_revoked : w.revoked = false
  nonce_fresh : nonceFresh
  unexpired : now ≤ w.expiry

/-- Recovery execution is conjunctive and does not require CURRENT. -/
structure RestoreExecutable
    (b : Bundle)
    (r : Replica)
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh compatible predecessor : Prop) : Prop where
  recoverable_ok : Recoverable b r
  compatible_ok : compatible
  recovery_authority_ok :
    ValidRecovery authorized w b.byteDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh
  predecessor_ok : predecessor

theorem restore_requires_recoverable
    {b : Bundle} {r : Replica} {authorized : RecoveryWitness → Prop} {w : RecoveryWitness}
    {targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat}
    {nonceFresh compatible predecessor : Prop}
    (h : RestoreExecutable b r authorized w targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh compatible predecessor) :
    Recoverable b r :=
  h.recoverable_ok

theorem restore_requires_recovery_authority
    {b : Bundle} {r : Replica} {authorized : RecoveryWitness → Prop} {w : RecoveryWitness}
    {targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat}
    {nonceFresh compatible predecessor : Prop}
    (h : RestoreExecutable b r authorized w targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh compatible predecessor) :
    ValidRecovery authorized w b.byteDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh :=
  h.recovery_authority_ok

/-- Ordinary runtime authorization can exist while the recovery authority store is empty. -/
theorem runtime_recovery_authority_separation :
    ∃ w : RuntimeWitness,
      RuntimeAuthorized (fun _ => True) w ∧
      ¬ ∃ rw : RecoveryWitness, (fun _ : RecoveryWitness => False) rw := by
  refine ⟨{ id := 1 }, trivial, ?_⟩
  simp

theorem recovery_witness_bundle_mismatch_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hMismatch : w.bundleDigest ≠ bundleDigest) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  exact hMismatch h.bundle_ok

theorem recovery_witness_consumed_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hConsumed : w.consumed = true) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  simpa [hConsumed] using h.not_consumed

theorem recovery_witness_revoked_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hRevoked : w.revoked = true) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  simpa [hRevoked] using h.not_revoked

theorem recovery_witness_replay_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hReplay : ¬ nonceFresh) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  exact hReplay h.nonce_fresh

theorem recovery_witness_expired_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hExpired : w.expiry < now) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  exact Nat.not_le_of_lt hExpired h.unexpired

theorem recovery_witness_wrong_policy_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hMismatch : w.policyDigest ≠ policyDigest) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  exact hMismatch h.policy_ok

theorem recovery_witness_wrong_epoch_invalid
    (authorized : RecoveryWitness → Prop)
    (w : RecoveryWitness)
    (bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now : Nat)
    (nonceFresh : Prop)
    (hMismatch : w.authorityEpoch ≠ authorityEpoch) :
    ¬ ValidRecovery authorized w bundleDigest targetStateDigest lineageId policyDigest authorityEpoch nonce now nonceFresh := by
  intro h
  exact hMismatch h.epoch_ok

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
    ∃ b : Bundle, ∃ r : Replica, Exact b r ∧ ¬ Immutable r := by
  let s : Snapshot := { lineageId := 1, stateDigest := 10 }
  let b : Bundle := { byteDigest := 7, snapshot := s }
  let r : Replica := {
    byteDigest := 7
    readable := true
    immutable := false
    configuredImmutable := false
    enforcedImmutable := false
  }
  refine ⟨b, r, ?_, ?_⟩
  · rfl
  · simp [Immutable, ProviderEnforcedImmutable, r]

/-- CM-RCCA-02: an immutable object can contain the wrong bytes. -/
theorem cm_immutable_wrong_bytes :
    ∃ b : Bundle, ∃ r : Replica, Immutable r ∧ ¬ Exact b r := by
  let s : Snapshot := { lineageId := 1, stateDigest := 10 }
  let b : Bundle := { byteDigest := 7, snapshot := s }
  let r : Replica := {
    byteDigest := 8
    readable := true
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  refine ⟨b, r, ?_, ?_⟩
  · simp [Immutable, ProviderEnforcedImmutable, r]
  · simp [Exact, b, r]

/-- CM-RCCA-03: exact immutable historical evidence can be superseded. -/
theorem cm_exact_immutable_but_superseded :
    ∃ b : Bundle, ∃ r : Replica, ∃ priorCurrent authenticatedCurrent : Snapshot,
      Exact b r ∧ Immutable r ∧ HistoricalValid b priorCurrent authenticatedCurrent true ∧
      ¬ Current b authenticatedCurrent := by
  let priorCurrent : Snapshot := { lineageId := 1, stateDigest := 10 }
  let authenticatedCurrent : Snapshot := { lineageId := 1, stateDigest := 11 }
  let b : Bundle := { byteDigest := 7, snapshot := priorCurrent }
  let r : Replica := {
    byteDigest := 7
    readable := true
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  refine ⟨b, r, priorCurrent, authenticatedCurrent, ?_, ?_, ?_, ?_⟩
  · rfl
  · simp [Immutable, ProviderEnforcedImmutable, r]
  · simp [HistoricalValid, Current, b, priorCurrent, authenticatedCurrent]
  · exact superseded_bundle_not_current b priorCurrent authenticatedCurrent rfl (by decide)

/-- CM-RCCA-04: currentness does not imply readable recoverability. -/
theorem cm_current_but_unreadable :
    ∃ b : Bundle, ∃ r : Replica, ∃ authenticatedCurrent : Snapshot,
      Current b authenticatedCurrent ∧ ¬ Recoverable b r := by
  let authenticatedCurrent : Snapshot := { lineageId := 1, stateDigest := 10 }
  let b : Bundle := { byteDigest := 7, snapshot := authenticatedCurrent }
  let r : Replica := {
    byteDigest := 7
    readable := false
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  refine ⟨b, r, authenticatedCurrent, ?_, ?_⟩
  · rfl
  · simp [Recoverable, Exact, Readable, r]

/-- CM-RCCA-05: recoverability does not mint recovery authority. -/
theorem cm_recoverable_without_recovery_witness :
    ∃ b : Bundle, ∃ r : Replica,
      Recoverable b r ∧
      ¬ ∃ w : RecoveryWitness,
        ValidRecovery (fun _ => False) w b.byteDigest 20 b.snapshot.lineageId 30 1 40 0 True := by
  let s : Snapshot := { lineageId := 1, stateDigest := 10 }
  let b : Bundle := { byteDigest := 7, snapshot := s }
  let r : Replica := {
    byteDigest := 7
    readable := true
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  refine ⟨b, r, ?_, ?_⟩
  · simp [Recoverable, Exact, Readable, b, r]
  · intro h
    rcases h with ⟨w, hw⟩
    exact hw.authorized_ok

/-- CM-RCCA-06: runtime authority does not become recovery authority. -/
theorem cm_runtime_token_not_recovery_token :
    ∃ w : RuntimeWitness,
      RuntimeAuthorized (fun _ => True) w ∧
      ¬ ∃ rw : RecoveryWitness, (fun _ : RecoveryWitness => False) rw :=
  runtime_recovery_authority_separation

/-- CM-RCCA-07: a recovery witness for another bundle is invalid here. -/
theorem cm_recovery_witness_wrong_bundle :
    ∃ b : Bundle, ∃ r : Replica, ∃ w : RecoveryWitness,
      Recoverable b r ∧
      ¬ ValidRecovery (fun _ => True) w b.byteDigest 20 b.snapshot.lineageId 30 1 40 0 True := by
  let s : Snapshot := { lineageId := 1, stateDigest := 10 }
  let b : Bundle := { byteDigest := 7, snapshot := s }
  let r : Replica := {
    byteDigest := 7
    readable := true
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  let w : RecoveryWitness := {
    bundleDigest := 8
    targetStateDigest := 20
    lineageId := 1
    policyDigest := 30
    authorityEpoch := 1
    nonce := 40
    expiry := 10
    consumed := false
    revoked := false
  }
  refine ⟨b, r, w, ?_, ?_⟩
  · simp [Recoverable, Exact, Readable, b, r]
  · apply recovery_witness_bundle_mismatch_invalid
    simp [b, w]

/-- CM-RCCA-08: stale policy or epoch requires revalidation. -/
theorem cm_stale_policy_or_epoch :
    ∃ w : RecoveryWitness,
      ValidRecovery (fun _ => True) w 7 20 1 30 4 40 0 True ∧
      ¬ ValidRecovery (fun _ => True) w 7 20 1 31 4 40 0 True := by
  let w : RecoveryWitness := {
    bundleDigest := 7
    targetStateDigest := 20
    lineageId := 1
    policyDigest := 30
    authorityEpoch := 4
    nonce := 40
    expiry := 10
    consumed := false
    revoked := false
  }
  refine ⟨w, ?_, ?_⟩
  · exact {
      authorized_ok := trivial
      bundle_ok := rfl
      target_ok := rfl
      lineage_ok := rfl
      policy_ok := rfl
      epoch_ok := rfl
      nonce_ok := rfl
      not_consumed := rfl
      not_revoked := rfl
      nonce_fresh := trivial
      unexpired := by decide
    }
  · apply recovery_witness_wrong_policy_invalid
    simp [w]

/-- CM-RCCA-09: configured immutability can lack provider enforcement. -/
theorem cm_configured_not_enforced :
    ∃ r : Replica, ConfiguredImmutable r ∧ ¬ ProviderEnforcedImmutable r :=
  configured_immutability_not_enforcement

/-- CM-RCCA-10: a non-current historical bundle can be explicitly authorized for rollback. -/
theorem cm_authorized_historical_rollback :
    ∃ b : Bundle, ∃ r : Replica, ∃ w : RecoveryWitness,
      ∃ priorCurrent authenticatedCurrent : Snapshot,
      HistoricalValid b priorCurrent authenticatedCurrent true ∧
      ¬ Current b authenticatedCurrent ∧
      RestoreExecutable b r (fun x => x = w) w 200 priorCurrent.lineageId 300 4 400 0 True True True := by
  let priorCurrent : Snapshot := { lineageId := 1, stateDigest := 10 }
  let authenticatedCurrent : Snapshot := { lineageId := 1, stateDigest := 11 }
  let b : Bundle := { byteDigest := 55, snapshot := priorCurrent }
  let r : Replica := {
    byteDigest := 55
    readable := true
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  let w : RecoveryWitness := {
    bundleDigest := 55
    targetStateDigest := 200
    lineageId := 1
    policyDigest := 300
    authorityEpoch := 4
    nonce := 400
    expiry := 10
    consumed := false
    revoked := false
  }
  refine ⟨b, r, w, priorCurrent, authenticatedCurrent, ?_, ?_, ?_⟩
  · simp [HistoricalValid, Current, b, priorCurrent, authenticatedCurrent]
  · exact superseded_bundle_not_current b priorCurrent authenticatedCurrent rfl (by decide)
  · exact {
      recoverable_ok := by simp [Recoverable, Exact, Readable, b, r]
      compatible_ok := trivial
      recovery_authority_ok := {
        authorized_ok := rfl
        bundle_ok := rfl
        target_ok := rfl
        lineage_ok := rfl
        policy_ok := rfl
        epoch_ok := rfl
        nonce_ok := rfl
        not_consumed := rfl
        not_revoked := rfl
        nonce_fresh := trivial
        unexpired := by decide
      }
      predecessor_ok := trivial
    }

/-- CM-RCCA-11: strong custody cannot compensate for bottom authority. -/
theorem cm_strong_custody_without_authority :
    ClaimCeiling .strong .strong .strong .bottom .strong = .bottom :=
  claim_ceiling_authority_bottom .strong .strong .strong .strong

/-- CM-RCCA-12: superseded material can persist while empty recovery authority prevents auto-execution. -/
theorem cm_supersession_with_audit_persistence :
    ∃ b : Bundle, ∃ r : Replica, ∃ priorCurrent authenticatedCurrent : Snapshot,
      HistoricalValid b priorCurrent authenticatedCurrent true ∧
      ¬ Current b authenticatedCurrent ∧
      ¬ ∃ w : RecoveryWitness,
        RestoreExecutable b r (fun _ => False) w 200 priorCurrent.lineageId 300 4 400 0 True True True := by
  let priorCurrent : Snapshot := { lineageId := 1, stateDigest := 10 }
  let authenticatedCurrent : Snapshot := { lineageId := 1, stateDigest := 11 }
  let b : Bundle := { byteDigest := 55, snapshot := priorCurrent }
  let r : Replica := {
    byteDigest := 55
    readable := true
    immutable := true
    configuredImmutable := true
    enforcedImmutable := true
  }
  refine ⟨b, r, priorCurrent, authenticatedCurrent, ?_, ?_, ?_⟩
  · simp [HistoricalValid, Current, b, priorCurrent, authenticatedCurrent]
  · exact superseded_bundle_not_current b priorCurrent authenticatedCurrent rfl (by decide)
  · intro h
    rcases h with ⟨w, hw⟩
    exact hw.recovery_authority_ok.authorized_ok

end RCCA
