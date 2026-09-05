import Mathlib

set_option autoImplicit false

namespace ResearchMathP0

/-- Ring-normalization canary: a nontrivial polynomial identity over the reals. -/
theorem ring_identity (a b : ℝ) :
    (a + b)^2 = a^2 + 2 * a * b + b^2 := by
  ring

/-- Positivity canary: every real square is nonnegative. -/
theorem square_nonnegative (x : ℝ) :
    0 ≤ x^2 := by
  positivity

/-- Natural-number algebra canary. -/
theorem nat_identity (n : ℕ) :
    (n + 1)^2 = n^2 + 2 * n + 1 := by
  ring

#check ring_identity
#check square_nonnegative
#check nat_identity

end ResearchMathP0
