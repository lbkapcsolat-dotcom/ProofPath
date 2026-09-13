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
