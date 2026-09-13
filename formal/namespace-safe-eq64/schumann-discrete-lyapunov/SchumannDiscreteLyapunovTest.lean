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
