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

end SchumannDiscreteLyapunovGate
