import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecificLimits.Normed
import Mathlib.Tactic

namespace SchumannDiscreteLyapunovGate

set_option autoImplicit false

/--
For the scalar discrete update `e⁺ = ρ e`, if `|ρ| ≤ q ≤ 1`, then the
quadratic Lyapunov candidate `V(e) = e²` contracts by at most `q²` and is
therefore nonincreasing.
-/
theorem schumann_discrete_lyapunov_bound_certificate
    {e rho q : ℝ}
    (hq0 : 0 ≤ q)
    (hq1 : q ≤ 1)
    (hrho : |rho| ≤ q) :
    (rho * e)^2 ≤ q^2 * e^2 ∧
      q^2 * e^2 ≤ e^2 := by
  have hrange : -q ≤ rho ∧ rho ≤ q := abs_le.mp hrho
  have hqMinusRho : 0 ≤ q - rho := sub_nonneg.mpr hrange.2
  have hqPlusRho : 0 ≤ q + rho := by
    linarith [hrange.1]
  have hprodRho : 0 ≤ (q - rho) * (q + rho) :=
    mul_nonneg hqMinusRho hqPlusRho
  have hrhoSq : rho^2 ≤ q^2 := by
    nlinarith [hprodRho]
  have heSq : 0 ≤ e^2 := sq_nonneg e
  have hcontract : (rho * e)^2 ≤ q^2 * e^2 := by
    calc
      (rho * e)^2 = rho^2 * e^2 := by ring
      _ ≤ q^2 * e^2 := mul_le_mul_of_nonneg_right hrhoSq heSq
  have hOneMinusQ : 0 ≤ 1 - q := sub_nonneg.mpr hq1
  have hOnePlusQ : 0 ≤ 1 + q := by
    linarith
  have hprodQ : 0 ≤ (1 - q) * (1 + q) :=
    mul_nonneg hOneMinusQ hOnePlusQ
  have hqSq : q^2 ≤ 1 := by
    nlinarith [hprodQ]
  have hnonincrease : q^2 * e^2 ≤ e^2 := by
    calc
      q^2 * e^2 ≤ 1 * e^2 := mul_le_mul_of_nonneg_right hqSq heSq
      _ = e^2 := by ring
  exact ⟨hcontract, hnonincrease⟩

/--
Iterating the one-step scalar contraction gives geometric decay of the
quadratic Lyapunov candidate after `n` steps.
-/
theorem schumann_discrete_lyapunov_n_step_geometric_decay_certificate
    {e0 rho q : ℝ} (n : ℕ)
    (hq0 : 0 ≤ q)
    (hq1 : q ≤ 1)
    (hrho : |rho| ≤ q) :
    (rho^n * e0)^2 ≤ q^(2 * n) * e0^2 := by
  induction n with
  | zero =>
      norm_num
  | succ n ih =>
      have hstep :=
        (schumann_discrete_lyapunov_bound_certificate
          (e := rho^n * e0) (rho := rho) (q := q) hq0 hq1 hrho).1
      have hqSq : 0 ≤ q^2 := sq_nonneg q
      have hfactor : rho^(Nat.succ n) * e0 = rho * (rho^n * e0) := by
        rw [pow_succ]
        ring
      have hqfactor : q^(2 * Nat.succ n) = q^2 * q^(2 * n) := by
        rw [Nat.mul_succ, pow_add]
        ring
      calc
        (rho^(Nat.succ n) * e0)^2 = (rho * (rho^n * e0))^2 := by
          rw [hfactor]
        _ ≤ q^2 * (rho^n * e0)^2 := hstep
        _ ≤ q^2 * (q^(2 * n) * e0^2) :=
          mul_le_mul_of_nonneg_left ih hqSq
        _ = q^(2 * Nat.succ n) * e0^2 := by
          rw [hqfactor]
          ring

/--
Under the strict contraction envelope `0 ≤ q < 1` and `|ρ| ≤ q`, the scalar
modal error has quadratic Lyapunov energy converging to zero.
-/
theorem schumann_discrete_lyapunov_asymptotic_zero_certificate
    {e0 rho q : ℝ}
    (_hq0 : 0 ≤ q)
    (hq1 : q < 1)
    (hrho : |rho| ≤ q) :
    Filter.Tendsto (fun n : ℕ => (rho^n * e0)^2)
      Filter.atTop (nhds 0) := by
  have hrho1 : |rho| < 1 := lt_of_le_of_lt hrho hq1
  have hpow :
      Filter.Tendsto (fun n : ℕ => rho^n) Filter.atTop (nhds 0) :=
    tendsto_pow_atTop_nhds_zero_of_abs_lt_one hrho1
  have herr :
      Filter.Tendsto (fun n : ℕ => rho^n * e0) Filter.atTop (nhds 0) := by
    simpa using hpow.mul_const e0
  have hsq := herr.mul herr
  simpa [pow_two] using hsq

/--
The two-dimensional Sylvester criterion for a symmetric quadratic form.
This is kept explicit so the matrix Lyapunov certificate does not depend on
runtime matrix representations.
-/
theorem quadratic2_pos_of_sylvester
    {p11 p12 p22 x1 x2 : ℝ}
    (hp11 : 0 < p11)
    (hpdet : 0 < p11 * p22 - p12^2)
    (hx : x1 ≠ 0 ∨ x2 ≠ 0) :
    0 < p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2 := by
  by_cases hx2 : x2 = 0
  · have hx1 : x1 ≠ 0 := by
      rcases hx with hx1 | hx2'
      · exact hx1
      · exact False.elim (hx2' hx2)
    have hx1sq : 0 < x1^2 := sq_pos_of_ne_zero hx1
    simpa [hx2] using mul_pos hp11 hx1sq
  · have hx2sq : 0 < x2^2 := sq_pos_of_ne_zero hx2
    have hdetTerm : 0 < (p11 * p22 - p12^2) * x2^2 :=
      mul_pos hpdet hx2sq
    have hsq : 0 ≤ (p11 * x1 + p12 * x2)^2 := sq_nonneg _
    have hidentity :
        p11 * (p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2) =
          (p11 * x1 + p12 * x2)^2 +
            (p11 * p22 - p12^2) * x2^2 := by
      ring
    have hprod :
        0 < p11 * (p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2) := by
      rw [hidentity]
      nlinarith
    nlinarith

/--
For the two-dimensional linear state update `x⁺ = A x`, let `P` be symmetric
positive definite. If `P - Aᵀ P A` is also positive definite, equivalently
`Aᵀ P A - P` is negative definite, then the quadratic Lyapunov function is
positive away from the origin and decreases strictly in one discrete step.
-/
theorem schumann_discrete_lyapunov_2d_matrix_strict_decay_certificate
    {a11 a12 a21 a22 p11 p12 p22 x1 x2 : ℝ}
    (hp11 : 0 < p11)
    (hpdet : 0 < p11 * p22 - p12^2)
    (hD11 :
      0 < p11 - (p11 * a11^2 + 2 * p12 * a11 * a21 + p22 * a21^2))
    (hDdet :
      0 <
        (p11 - (p11 * a11^2 + 2 * p12 * a11 * a21 + p22 * a21^2)) *
          (p22 - (p11 * a12^2 + 2 * p12 * a12 * a22 + p22 * a22^2)) -
        (p12 -
          (p11 * a11 * a12 + p12 * (a11 * a22 + a21 * a12) +
            p22 * a21 * a22))^2)
    (hx : x1 ≠ 0 ∨ x2 ≠ 0) :
    0 < p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2 ∧
      p11 * (a11 * x1 + a12 * x2)^2 +
          2 * p12 * (a11 * x1 + a12 * x2) * (a21 * x1 + a22 * x2) +
          p22 * (a21 * x1 + a22 * x2)^2
        < p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2 := by
  let d11 : ℝ :=
    p11 - (p11 * a11^2 + 2 * p12 * a11 * a21 + p22 * a21^2)
  let d12 : ℝ :=
    p12 -
      (p11 * a11 * a12 + p12 * (a11 * a22 + a21 * a12) +
        p22 * a21 * a22)
  let d22 : ℝ :=
    p22 - (p11 * a12^2 + 2 * p12 * a12 * a22 + p22 * a22^2)
  have hVpos :
      0 < p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2 :=
    quadratic2_pos_of_sylvester hp11 hpdet hx
  have hD11' : 0 < d11 := by
    simpa [d11] using hD11
  have hDdet' : 0 < d11 * d22 - d12^2 := by
    simpa [d11, d12, d22] using hDdet
  have hDpos :
      0 < d11 * x1^2 + 2 * d12 * x1 * x2 + d22 * x2^2 :=
    quadratic2_pos_of_sylvester hD11' hDdet' hx
  have hdelta :
      d11 * x1^2 + 2 * d12 * x1 * x2 + d22 * x2^2 =
        (p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2) -
          (p11 * (a11 * x1 + a12 * x2)^2 +
            2 * p12 * (a11 * x1 + a12 * x2) * (a21 * x1 + a22 * x2) +
            p22 * (a21 * x1 + a22 * x2)^2) := by
    dsimp [d11, d12, d22]
    ring
  constructor
  · exact hVpos
  · rw [hdelta] at hDpos
    linarith

/--
Jury's three strict inequalities for a real monic quadratic imply that every
complex root, represented by real and imaginary coordinates, lies strictly
inside the unit disk.
-/
theorem quadratic_schur_stable_of_jury
    {trace det : ℝ}
    (hj1 : 0 < 1 - trace + det)
    (hj2 : 0 < 1 + trace + det)
    (hj3 : det < 1) :
    ∀ xr xi : ℝ,
      xr^2 - xi^2 - trace * xr + det = 0 →
      (2 * xr - trace) * xi = 0 →
      xr^2 + xi^2 < 1 := by
  intro xr xi hre him
  by_cases hxi : xi = 0
  · subst xi
    have hxrlt : xr < 1 := by
      by_contra hnot
      have hxr1 : 1 ≤ xr := le_of_not_gt hnot
      have hfac : 0 < (1 - xr) * (1 + xr - trace) := by
        nlinarith [hre, hj1]
      rcases (mul_pos_iff.mp hfac) with hpos | hneg
      · nlinarith [hpos.1]
      · have hprod : 0 ≤ (xr - 1) * (trace - xr) :=
          mul_nonneg (sub_nonneg.mpr hxr1) (by linarith [hneg.2])
        nlinarith [hre, hj3, hneg.2, hprod]
    have hxrgt : -1 < xr := by
      by_contra hnot
      have hxrle : xr ≤ -1 := le_of_not_gt hnot
      have hfac : 0 < (1 + xr) * (1 - xr + trace) := by
        nlinarith [hre, hj2]
      rcases (mul_pos_iff.mp hfac) with hpos | hneg
      · nlinarith [hpos.1]
      · have hprod : 0 ≤ (-xr - 1) * (xr - trace) :=
          mul_nonneg (by linarith [hxrle]) (by linarith [hneg.2])
        nlinarith [hre, hj3, hneg.2, hprod]
    have hunit : 0 < (1 - xr) * (1 + xr) :=
      mul_pos (by linarith) (by linarith)
    nlinarith [hunit]
  · have hcoef : 2 * xr - trace = 0 := by
      rcases mul_eq_zero.mp him with hcoef | hzero
      · exact hcoef
      · exact False.elim (hxi hzero)
    nlinarith [hre, hj3]

/--
For the semi-implicit discretization of the damped oscillator

`v⁺ = (1 - 2 ζω Δt) v - Δt ω² x`
`x⁺ = x + Δt v⁺`,

the explicit state matrix is tied to `(Δt, ω, ζ)`. Under transparent strict
step-size certificates, the characteristic quadratic is Schur stable and the
constructive choice `P = diag(ω², 1)` satisfies `P - Aᵀ P A ≻ 0`, giving
strict one-step Lyapunov decay away from the origin.
-/
theorem schumann_2d_damped_oscillator_semiimplicit_schur_lyapunov_bridge_certificate
    {dt omega zeta x1 x2 : ℝ}
    (hdt : 0 < dt)
    (homega : 0 < omega)
    (hzeta : 0 < zeta)
    (hr1 : dt * omega < 1)
    (hJury : (dt * omega)^2 + 4 * zeta * (dt * omega) < 4)
    (hLyap : (dt * omega) * (4 * zeta^2 + 1) < 4 * zeta)
    (hx : x1 ≠ 0 ∨ x2 ≠ 0) :
    (∀ xr xi : ℝ,
      xr^2 - xi^2 -
          (2 - (dt * omega)^2 - 2 * zeta * (dt * omega)) * xr +
          (1 - 2 * zeta * (dt * omega)) = 0 →
      (2 * xr - (2 - (dt * omega)^2 - 2 * zeta * (dt * omega))) * xi = 0 →
      xr^2 + xi^2 < 1) ∧
    0 < omega^2 * x1^2 + x2^2 ∧
      omega^2 *
          ((1 - (dt * omega)^2) * x1 +
            dt * (1 - 2 * zeta * dt * omega) * x2)^2 +
        (-dt * omega^2 * x1 + (1 - 2 * zeta * dt * omega) * x2)^2
        < omega^2 * x1^2 + x2^2 := by
  let r : ℝ := dt * omega
  let trace : ℝ := 2 - r^2 - 2 * zeta * r
  let det : ℝ := 1 - 2 * zeta * r
  let a11 : ℝ := 1 - r^2
  let a12 : ℝ := dt * (1 - 2 * zeta * r)
  let a21 : ℝ := -dt * omega^2
  let a22 : ℝ := 1 - 2 * zeta * r
  have hrpos : 0 < r := by
    simpa [r] using mul_pos hdt homega
  have hr2pos : 0 < r^2 := by
    have hmul : 0 < r * r := mul_pos hrpos hrpos
    nlinarith
  have hj1 : 0 < 1 - trace + det := by
    dsimp [trace, det]
    nlinarith [hr2pos]
  have hj2 : 0 < 1 + trace + det := by
    dsimp [trace, det, r]
    nlinarith [hJury]
  have hzrp : 0 < 2 * zeta * r := by
    exact mul_pos (mul_pos (by norm_num) hzeta) hrpos
  have hj3 : det < 1 := by
    dsimp [det]
    linarith
  have hschur := quadratic_schur_stable_of_jury hj1 hj2 hj3
  have homegaSq : 0 < omega^2 := by
    have hmul : 0 < omega * omega := mul_pos homega homega
    nlinarith
  have hp11 : 0 < omega^2 := homegaSq
  have hpdet : 0 < omega^2 * (1 : ℝ) - 0^2 := by
    norm_num
    exact hp11
  have hOneMinusRSq : 0 < 1 - r^2 := by
    have hplus : 0 < 1 + r := by
      linarith
    have hprod : 0 < (1 - r) * (1 + r) :=
      mul_pos (sub_pos.mpr (by simpa [r] using hr1)) hplus
    nlinarith [hprod]
  have hD11 :
      0 < omega^2 -
        (omega^2 * a11^2 + 2 * 0 * a11 * a21 + (1 : ℝ) * a21^2) := by
    have hfactor :
        omega^2 -
            (omega^2 * a11^2 + 2 * 0 * a11 * a21 + (1 : ℝ) * a21^2) =
          dt^2 * omega^4 * (1 - r^2) := by
      dsimp [a11, a21, r]
      ring
    rw [hfactor]
    positivity
  have hgap : 0 < 4 * zeta - r * (4 * zeta^2 + 1) := by
    simpa [r] using sub_pos.mpr hLyap
  have hDdet :
      0 <
        (omega^2 -
            (omega^2 * a11^2 + 2 * 0 * a11 * a21 + (1 : ℝ) * a21^2)) *
          ((1 : ℝ) -
            (omega^2 * a12^2 + 2 * 0 * a12 * a22 + (1 : ℝ) * a22^2)) -
        (0 -
          (omega^2 * a11 * a12 + 0 * (a11 * a22 + a21 * a12) +
            (1 : ℝ) * a21 * a22))^2 := by
    have hfactor :
        (omega^2 -
            (omega^2 * a11^2 + 2 * 0 * a11 * a21 + (1 : ℝ) * a21^2)) *
          ((1 : ℝ) -
            (omega^2 * a12^2 + 2 * 0 * a12 * a22 + (1 : ℝ) * a22^2)) -
        (0 -
          (omega^2 * a11 * a12 + 0 * (a11 * a22 + a21 * a12) +
            (1 : ℝ) * a21 * a22))^2 =
          dt^3 * omega^5 * (4 * zeta - r * (4 * zeta^2 + 1)) := by
      dsimp [a11, a12, a21, a22, r]
      ring
    rw [hfactor]
    positivity
  have hstrict :=
    schumann_discrete_lyapunov_2d_matrix_strict_decay_certificate
      (a11 := a11) (a12 := a12) (a21 := a21) (a22 := a22)
      (p11 := omega^2) (p12 := 0) (p22 := 1)
      (x1 := x1) (x2 := x2) hp11 hpdet hD11 hDdet hx
  constructor
  · simpa [trace, det, r] using hschur
  · constructor
    · simpa [a11, a12, a21, a22, r] using hstrict.1
    · have hdec := hstrict.2
      dsimp [a11, a12, a21, a22, r] at hdec
      ring_nf at hdec ⊢
      exact hdec

end SchumannDiscreteLyapunovGate
