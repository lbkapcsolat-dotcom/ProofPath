import Mathlib.Data.Real.Basic
import Mathlib.Tactic

namespace GECConvexIntervalGate

set_option autoImplicit false

/-- A convex combination of two points in a closed real interval remains in that interval. -/
theorem gec_convex_interval_invariance
    {L U x u α : ℝ}
    (hxL : L ≤ x) (hxU : x ≤ U)
    (huL : L ≤ u) (huU : u ≤ U)
    (hα0 : 0 ≤ α) (hα1 : α ≤ 1) :
    L ≤ α * x + (1 - α) * u ∧
      α * x + (1 - α) * u ≤ U := by
  have hβ0 : 0 ≤ 1 - α := sub_nonneg.mpr hα1
  constructor
  · calc
      L = α * L + (1 - α) * L := by ring
      _ ≤ α * x + (1 - α) * u :=
        add_le_add
          (mul_le_mul_of_nonneg_left hxL hα0)
          (mul_le_mul_of_nonneg_left huL hβ0)
  · calc
      α * x + (1 - α) * u ≤ α * U + (1 - α) * U :=
        add_le_add
          (mul_le_mul_of_nonneg_left hxU hα0)
          (mul_le_mul_of_nonneg_left huU hβ0)
      _ = U := by ring

end GECConvexIntervalGate
