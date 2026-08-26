from sage.env import SAGE_VERSION
from sage.all import QQ, PolynomialRing, matrix, vector, crt, factor

assert SAGE_VERSION == "10.9", SAGE_VERSION
print("SageMath version:", SAGE_VERSION)

# Exact polynomial algebra over Q.
R = PolynomialRing(QQ, "x")
x = R.gen()
p = x**4 - 1
expected = (x - 1) * (x + 1) * (x**2 + 1)
assert p == expected
fac = p.factor()
print("factor(x^4 - 1) =", fac)
assert fac.prod() == p

# Exact rational linear algebra: no floating-point tolerance involved.
A = matrix(QQ, [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
b = vector(QQ, [8, -11, -3])
sol = A.solve_right(b)
print("exact linear solution =", sol)
assert A * sol == b
assert sol == vector(QQ, [2, 3, -1])

# Exact number-theory canaries.
r = crt([2, 3, 2], [3, 5, 7])
print("CRT solution =", r)
assert r == 23

n = 2**32 - 1
f = factor(n)
print("factor(2^32 - 1) =", f)
assert f.prod() == n

print("P2-D SAGEMATH INDEPENDENT CAS = PASS")
