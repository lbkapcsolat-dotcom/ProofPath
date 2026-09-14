# Namespace-Safe EQ64 Formal/Reference Gate

This isolated subsystem separates abstract B6/Q6 structural equivalence from semantic namespace authority.

## Mandatory verification

Run from this directory:

`lake build`

`lake env lean NamespaceSafeEQ64Test.lean`

`python -m unittest discover -s tests -v`

The real `X_AIPRBG_6GATE_DIAGNOSTIC_V1 -> ESS_EQ64_6D_KERNEL` canary must produce 720/720 structural PASS and zero semantic PASS without C1-C11 axis evidence. The synthetic control must produce exactly one semantic PASS and 719 DENY.

## Claim ceiling

A fully passing run establishes only:

`PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT`

It does not establish empirical truth, physical correctness, historical semantic equivalence, global authority, general runtime admission, or production readiness.

`RUNTIME_BIND = FALSE` in this package.
