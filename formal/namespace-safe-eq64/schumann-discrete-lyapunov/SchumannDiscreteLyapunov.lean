import Mathlib.Data.Real.Basic
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

end SchumannDiscreteLyapunovGate
