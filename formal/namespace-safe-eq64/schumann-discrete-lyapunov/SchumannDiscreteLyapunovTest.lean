import SchumannDiscreteLyapunov

open SchumannDiscreteLyapunovGate

#check schumann_discrete_lyapunov_bound_certificate

example {e rho q : ℝ}
    (hq0 : 0 ≤ q)
    (hq1 : q ≤ 1)
    (hrho : |rho| ≤ q) :
    (rho * e)^2 ≤ q^2 * e^2 ∧
      q^2 * e^2 ≤ e^2 :=
  schumann_discrete_lyapunov_bound_certificate hq0 hq1 hrho

#check schumann_discrete_lyapunov_n_step_geometric_decay_certificate

example {e0 rho q : ℝ} (n : ℕ)
    (hq0 : 0 ≤ q)
    (hq1 : q ≤ 1)
    (hrho : |rho| ≤ q) :
    (rho^n * e0)^2 ≤ q^(2 * n) * e0^2 :=
  schumann_discrete_lyapunov_n_step_geometric_decay_certificate n hq0 hq1 hrho

#check schumann_discrete_lyapunov_asymptotic_zero_certificate

example {e0 rho q : ℝ}
    (hq0 : 0 ≤ q)
    (hq1 : q < 1)
    (hrho : |rho| ≤ q) :
    Filter.Tendsto (fun n : ℕ => (rho^n * e0)^2)
      Filter.atTop (nhds 0) :=
  schumann_discrete_lyapunov_asymptotic_zero_certificate hq0 hq1 hrho

#check schumann_discrete_lyapunov_2d_matrix_strict_decay_certificate

example
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
        < p11 * x1^2 + 2 * p12 * x1 * x2 + p22 * x2^2 :=
  schumann_discrete_lyapunov_2d_matrix_strict_decay_certificate
    hp11 hpdet hD11 hDdet hx

#check schumann_2d_damped_oscillator_semiimplicit_schur_lyapunov_bridge_certificate

example
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
        < omega^2 * x1^2 + x2^2 :=
  schumann_2d_damped_oscillator_semiimplicit_schur_lyapunov_bridge_certificate
    hdt homega hzeta hr1 hJury hLyap hx

#check discrete_lyapunov_general_2d_jury_schur_exists_certificate

example {a b c d : ℝ}
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
          < p * x1^2 + 2 * q * x1 * x2 + r * x2^2 :=
  discrete_lyapunov_general_2d_jury_schur_exists_certificate hj1 hj2 hj3
