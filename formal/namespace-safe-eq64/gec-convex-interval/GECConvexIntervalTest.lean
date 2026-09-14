import GECConvexInterval

open GECConvexIntervalGate

/-! LEAN_GEC_CONVEX_INTERVAL_INVARIANCE_V1: isolated RED contract. -/
#check gec_convex_interval_invariance

example {L U x u α : ℝ}
    (hxL : L ≤ x) (hxU : x ≤ U)
    (huL : L ≤ u) (huU : u ≤ U)
    (hα0 : 0 ≤ α) (hα1 : α ≤ 1) :
    L ≤ α * x + (1 - α) * u ∧
      α * x + (1 - α) * u ≤ U :=
  gec_convex_interval_invariance hxL hxU huL huU hα0 hα1
