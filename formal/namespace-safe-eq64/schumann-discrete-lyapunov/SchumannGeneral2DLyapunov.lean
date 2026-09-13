import SchumannDiscreteLyapunov

namespace SchumannDiscreteLyapunovGate

set_option autoImplicit false

/--
For a real 2×2 matrix `A = [[a,b],[c,d]]`, the strict Jury inequalities for
its characteristic polynomial construct an explicit symmetric positive
definite solution of the discrete Lyapunov equation

`P - Aᵀ P A = I`.

The construction is rational in the entries of `A`.  It is written through
trace/determinant invariants and the basis `I`, `A + Aᵀ`, `Aᵀ A`, which keeps
the positivity proof auditable while remaining exactly equivalent to explicit
rational entries `p`, `q`, `r`.
-/
theorem discrete_lyapunov_general_2d_jury_schur_exists_certificate
    {a b c d : ℝ}
    (hj1 : 0 < 1 - (a + d) + (a * d - b * c))
    (hj2 : 0 < 1 + (a + d) + (a * d - b * c))
    (hj3 : a * d - b * c < 1) :
    ∃ p q r : ℝ,
      0 < p ∧
      0 < p * r - q^2 ∧
      p - (p * a^2 + 2 * q * a * c + r * c^2) = 1 ∧
      q - (p * a * b + q * (a * d + c * b) + r * c * d) = 0 ∧
      r - (p * b^2 + 2 * q * b * d + r * d^2) = 1 ∧
      ∀ x1 x2 : ℝ, x1 ≠ 0 ∨ x2 ≠ 0 →
        p * (a * x1 + b * x2)^2 +
            2 * q * (a * x1 + b * x2) * (c * x1 + d * x2) +
            r * (c * x1 + d * x2)^2
          < p * x1^2 + 2 * q * x1 * x2 + r * x2^2 := by
  let t : ℝ := a + d
  let delta : ℝ := a * d - b * c
  let den : ℝ := (1 - delta) * ((1 + delta)^2 - t^2)
  let gamma : ℝ := (1 + delta) / den
  let beta : ℝ := -(t * delta) / den
  let alpha : ℝ := 1 + gamma * delta^2
  let p : ℝ := alpha + 2 * beta * a + gamma * (a^2 + c^2)
  let q : ℝ := beta * (b + c) + gamma * (a * b + c * d)
  let r : ℝ := alpha + 2 * beta * d + gamma * (b^2 + d^2)

  have hj1' : 0 < 1 - t + delta := by
    simpa [t, delta] using hj1
  have hj2' : 0 < 1 + t + delta := by
    simpa [t, delta] using hj2
  have hj3' : delta < 1 := by
    simpa [delta] using hj3
  have hOnePlus : 0 < 1 + delta := by
    linarith [hj1', hj2']
  have hOneMinus : 0 < 1 - delta := by
    linarith
  have hband : 0 < (1 + delta)^2 - t^2 := by
    have hprod : 0 < (1 - t + delta) * (1 + t + delta) :=
      mul_pos hj1' hj2'
    nlinarith [hprod]
  have hdenpos : 0 < den := by
    simpa [den] using mul_pos hOneMinus hband
  have hdenne : den ≠ 0 := ne_of_gt hdenpos
  have hgammapos : 0 < gamma := by
    exact div_pos hOnePlus hdenpos

  let k : ℝ := t * delta / (1 + delta)
  let eta : ℝ := delta^2 - k^2
  have hOnePlusSq : 0 < (1 + delta)^2 := by
    exact sq_pos_of_ne_zero (ne_of_gt hOnePlus)
  have hratio : 0 < ((1 + delta)^2 - t^2) / (1 + delta)^2 :=
    div_pos hband hOnePlusSq
  have hetaIdentity :
      eta = delta^2 * (((1 + delta)^2 - t^2) / (1 + delta)^2) := by
    dsimp [eta, k]
    field_simp [ne_of_gt hOnePlus]
  have heta : 0 ≤ eta := by
    rw [hetaIdentity]
    exact mul_nonneg (sq_nonneg delta) (le_of_lt hratio)
  have hbeta : beta = -gamma * k := by
    dsimp [beta, gamma, k]
    field_simp [hdenne, ne_of_gt hOnePlus]

  have hquadIdentity (x1 x2 : ℝ) :
      p * x1^2 + 2 * q * x1 * x2 + r * x2^2 =
        x1^2 + x2^2 +
          gamma *
            ((a * x1 + b * x2 - k * x1)^2 +
              (c * x1 + d * x2 - k * x2)^2 +
              eta * (x1^2 + x2^2)) := by
    dsimp [p, q, r, alpha, eta]
    rw [hbeta]
    ring

  have hquadPos :
      ∀ x1 x2 : ℝ, x1 ≠ 0 ∨ x2 ≠ 0 →
        0 < p * x1^2 + 2 * q * x1 * x2 + r * x2^2 := by
    intro x1 x2 hx
    have hnorm : 0 < x1^2 + x2^2 := by
      rcases hx with hx1 | hx2
      · have hx1sq : 0 < x1^2 := sq_pos_of_ne_zero hx1
        nlinarith [sq_nonneg x2]
      · have hx2sq : 0 < x2^2 := sq_pos_of_ne_zero hx2
        nlinarith [sq_nonneg x1]
    have hbracket :
        0 ≤
          (a * x1 + b * x2 - k * x1)^2 +
            (c * x1 + d * x2 - k * x2)^2 +
            eta * (x1^2 + x2^2) := by
      have h1 : 0 ≤ (a * x1 + b * x2 - k * x1)^2 := sq_nonneg _
      have h2 : 0 ≤ (c * x1 + d * x2 - k * x2)^2 := sq_nonneg _
      have h3 : 0 ≤ eta * (x1^2 + x2^2) :=
        mul_nonneg heta (le_of_lt hnorm)
      nlinarith
    rw [hquadIdentity]
    have hterm :
        0 ≤ gamma *
          ((a * x1 + b * x2 - k * x1)^2 +
            (c * x1 + d * x2 - k * x2)^2 +
            eta * (x1^2 + x2^2)) :=
      mul_nonneg (le_of_lt hgammapos) hbracket
    linarith

  have hp : 0 < p := by
    simpa using hquadPos 1 0 (Or.inl (by norm_num))
  have hpdet : 0 < p * r - q^2 := by
    have hv := hquadPos (-q) p (Or.inr (ne_of_gt hp))
    have hid :
        p * (-q)^2 + 2 * q * (-q) * p + r * p^2 =
          p * (p * r - q^2) := by
      ring
    rw [hid] at hv
    rcases mul_pos_iff.mp hv with hpos | hneg
    · exact hpos.2
    · exfalso
      linarith [hp, hneg.1]

  have hE11 :
      p - (p * a^2 + 2 * q * a * c + r * c^2) = 1 := by
    dsimp [p, q, r, alpha, beta, gamma]
    field_simp [hdenne]
    dsimp [den, t, delta]
    ring
  have hE12 :
      q - (p * a * b + q * (a * d + c * b) + r * c * d) = 0 := by
    dsimp [p, q, r, alpha, beta, gamma]
    field_simp [hdenne]
    dsimp [den, t, delta]
    ring
  have hE22 :
      r - (p * b^2 + 2 * q * b * d + r * d^2) = 1 := by
    dsimp [p, q, r, alpha, beta, gamma]
    field_simp [hdenne]
    dsimp [den, t, delta]
    ring

  have hD11 :
      0 < p - (p * a^2 + 2 * q * a * c + r * c^2) := by
    rw [hE11]
    norm_num
  have hDdet :
      0 <
        (p - (p * a^2 + 2 * q * a * c + r * c^2)) *
          (r - (p * b^2 + 2 * q * b * d + r * d^2)) -
        (q - (p * a * b + q * (a * d + c * b) + r * c * d))^2 := by
    rw [hE11, hE12, hE22]
    norm_num

  refine ⟨p, q, r, hp, hpdet, hE11, hE12, hE22, ?_⟩
  intro x1 x2 hx
  exact
    (schumann_discrete_lyapunov_2d_matrix_strict_decay_certificate
      (a11 := a) (a12 := b) (a21 := c) (a22 := d)
      (p11 := p) (p12 := q) (p22 := r)
      (x1 := x1) (x2 := x2)
      hp hpdet hD11 hDdet hx).2

end SchumannDiscreteLyapunovGate
