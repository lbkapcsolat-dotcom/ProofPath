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
