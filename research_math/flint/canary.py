from flint import arb, ctx

ctx.dps = 80


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# P0-B canary 1: sqrt(2) is computed as an Arb ball; squaring it must
# rigorously enclose the exact value 2, hence the residual must contain 0.
sqrt2 = arb(2).sqrt()
residual = sqrt2 * sqrt2 - 2
require(residual.contains(0), f"zero is not enclosed by residual: {residual}")
require(
    residual.abs_upper() < arb("1e-70"),
    f"residual enclosure is too wide: {residual}",
)

# P0-B canary 2: interval propagation through an inexact division/multiply
# round trip must still rigorously enclose the exact integer 1.
one_third = arb(1) / 3
roundtrip = one_third * 3
require(roundtrip.contains(1), f"1 is not enclosed by roundtrip: {roundtrip}")

# P0-B canary 3: expose a high-precision special-function enclosure so the
# CI log itself carries a human-readable numerical witness.
zeta3 = arb(3).zeta()

print("P0-B FLINT/ARB = PASS")
print("sqrt(2) ball:", sqrt2)
print("sqrt(2)^2 - 2 enclosure:", residual)
print("(1/3)*3 enclosure:", roundtrip)
print("zeta(3) enclosure:", zeta3)
