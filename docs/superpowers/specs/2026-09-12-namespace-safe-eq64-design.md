# Namespace-Safe EQ64 Formal/Reference Design

Date: 2026-09-12
Branch: `design/namespace-safe-eq64`
Status: DESIGN APPROVED IN CHAT, IMPLEMENTATION NOT STARTED

## 1. Purpose

Build a fail-closed namespace-safe bridge layer that separates abstract B6/Q6 structural equivalence from semantic-axis identity. A structural isomorphism, coordinate permutation, shared 64-state cardinality, or Hamming-graph equivalence must never be interpreted as semantic authority.

Approved sequence:

```text
FORMAL SPEC
  -> REFERENCE ENGINE
  -> 720 ADVERSARIAL CANARY
  -> POSITIVE CONTROL
  -> CONTENT-ADDRESSED RECEIPT
  -> RUNTIME BIND GATE
```

Runtime binding is outside this phase and must remain false.

## 2. Existing project pattern

The repository already has a Lean4 formalization pattern in `formal/rcca-lean4/`: typed structures, explicit predicates, theorem-level non-weakening properties, and separate Lean tests/countermodels. This subsystem follows the same separation: proof obligations in Lean; executable conformance and adversarial enumeration in an isolated reference implementation.

## 3. Scope

### In scope

- typed namespace model;
- B6/Q6 structural model over `{0,1}^6`;
- explicit polarity/order contract;
- structural mapping validation;
- semantic crosswalk evidence gate;
- TRI result model: PASS / HOLD / DENY;
- exhaustive 720 coordinate-permutation negative canary;
- one synthetic positive-control crosswalk;
- content-addressed machine receipt;
- explicit separation of formal proof from executable reference evidence.

### Out of scope

- active runtime imports or consumer wiring;
- production dependency or auto-registration;
- pointer mutation/promotion;
- global bind or runtime admission;
- empirical or physical validation;
- semantic truth claims about historical EQ64 families.

## 4. Canonical namespace identities

Both namespaces may share the carrier `B6 = {0,1}^6`, but their semantics are distinct.

### 4.1 `ESS_EQ64_6D_KERNEL`

Axes:

1. `energy_load`
2. `volatility`
3. `coherence`
4. `phase_stability`
5. `transient_headroom`
6. `lock_margin`

Raw polarity:

- axes 1-2: raw `1` means higher risk/burden;
- axes 3-6: raw `1` means higher protection/support.

Favorable-orientation normalization:

```text
N(b0,b1,b2,b3,b4,b5) = (1-b0, 1-b1, b2, b3, b4, b5)
```

Equivalently, XOR with `[1,1,0,0,0,0]`.

### 4.2 `X_AIPRBG_6GATE_DIAGNOSTIC_V1`

Axes:

1. Authority
2. Identity
3. Provenance
4. Runtime
5. Readback
6. Governance

This is an audit diagnostic namespace. It must not be called bare `EQ64` for semantic claims and must not inherit ESS operational axis meanings.

## 5. Formal model

A namespace is modeled as:

```text
N = (Id, Sigma, Pi, S, C)
```

where `Id` is namespace identity, `Sigma` the ordered semantic schema, `Pi` the polarity/order contract, `S` the structural class, and `C` the claim ceiling.

Shared abstract structural class:

```text
B6 = ({0,1}^6, meet, join, <=)
Q6 adjacency <=> HammingDistance(x,y) = 1
```

A coordinate permutation `pi in S6` induces `phi_pi : B6 -> B6`.

Structural validity requires:

```text
phi_pi(x meet y) = phi_pi(x) meet phi_pi(y)
phi_pi(x join y) = phi_pi(x) join phi_pi(y)
HammingDistance(x,y) = HammingDistance(phi_pi(x), phi_pi(y))
```

The key formal safety statement is not an untyped philosophical claim. The Lean model must make semantic authorization a separate proposition that requires explicit evidence. The theorem obligation is therefore:

```text
no_semantic_authorization_from_structure_alone
```

meaning: given only a structural isomorphism and no semantic-evidence witness, exact semantic authorization is not derivable.

## 6. Exact semantic crosswalk contract

A semantic crosswalk is a separate object:

```text
f : Sigma_source -> Sigma_target
```

Bijectivity is necessary but not sufficient. Exact semantic PASS requires all eleven criteria:

- `C1_SOURCE_IDENTITY`: exact source artifact and lineage identified.
- `C2_STRUCTURAL_CLASS`: structural class explicit and compatible.
- `C3_AXIS_COMPLETENESS`: all six source meanings explicit.
- `C4_POLARITY`: polarity/order explicit for all six axes.
- `C5_CONFLICT_FREE`: no unresolved aliases or semantic drift.
- `C6_BIJECTION_CANDIDATE`: one-to-one six-axis mapping exists.
- `C7_AXIS_EVIDENCE`: each source-target semantic equivalence has independent source-grounded evidence.
- `C8_ORDER_SEMANTICS`: semantic order is preserved, not merely graph adjacency.
- `C9_NO_POST_HOC_SELECTION`: mapping was not selected because it fit after inspection.
- `C10_GOVERNANCE_SCOPE`: governance permits the claimed scope.
- `C11_CLAIM_CEILING`: source claim ceiling is preserved.

Any missing criterion yields HOLD. Any explicit contradiction to a required criterion yields DENY.

## 7. TRI decision model

```text
PASS = all required evidence and compatibility obligations satisfied
HOLD = evidence insufficient for the positive claim
DENY = explicit contradiction, policy violation, or incompatible mapping proven
```

Unknown is never coerced to PASS.

Example:

```json
{
  "structural_status": "PASS",
  "semantic_status": "HOLD",
  "claim_ceiling": "STRUCTURAL_ONLY",
  "reason_codes": ["NO_AXIS_LEVEL_EVIDENCE"]
}
```

## 8. Approved file layout

```text
formal/namespace-safe-eq64/
├── NamespaceSafeEQ64.lean
├── NamespaceSafeEQ64Test.lean
├── lakefile.lean
├── lean-toolchain
├── README.md
├── reference/
│   ├── namespace_safe_engine.py
│   ├── permutation_canary_720.py
│   └── receipt.py
├── fixtures/
│   ├── ess_eq64_6d_kernel.json
│   ├── x_aiprbg_6gate.json
│   ├── synthetic_exact_a.json
│   └── synthetic_exact_b.json
├── schema/
│   ├── namespace.schema.json
│   ├── crosswalk_evidence.schema.json
│   └── canary_receipt.schema.json
└── tests/
    ├── test_structure.py
    ├── test_semantic_gate.py
    ├── test_720_canary.py
    └── test_positive_control.py
```

## 9. Lean proof obligations

`NamespaceSafeEQ64.lean` must define typed representations for:

```text
NamespaceId
Axis
AxisSchema
Polarity
StructuralClass
SemanticEvidence
Crosswalk
```

Minimum theorem obligations:

```text
coordinate_permutation_preserves_B6_structure
coordinate_permutation_preserves_Q6_hamming
no_semantic_authorization_from_structure_alone
missing_axis_evidence_blocks_exact_crosswalk
polarity_conflict_blocks_exact_crosswalk
namespace_identity_required
```

The formal layer must not assert that AIPRBG axes equal ESS operational axes. It proves separation and the requirements that must exist before semantic authorization can be admitted.

## 10. Reference engine interface

```python
validate_namespace(namespace)
normalize_polarity(namespace, state)
check_structural_mapping(source, target, permutation)
check_semantic_crosswalk(source, target, evidence, permutation)
classify_mapping(...)
```

The engine must never auto-match semantic axes, infer a best mapping, or treat positional equality as evidence.

## 11. 720-permutation negative canary

Enumerate all `6! = 720` coordinate permutations.

For real AIPRBG and ESS fixtures with no admitted axis-level semantic evidence:

```text
TOTAL_PERMUTATIONS = 720
STRUCTURAL_PASS = 720
SEMANTIC_PASS = 0
SEMANTIC_HOLD = 720
SEMANTIC_DENY = 0
UNEXPECTED_SEMANTIC_PASS = 0
```

The safety property is exact:

```text
unexpected_semantic_pass == 0
```

## 12. Synthetic positive control

Two synthetic namespaces contain one predeclared exact six-axis mapping with complete evidence and polarity compatibility.

Expected result:

```text
TOTAL_PERMUTATIONS = 720
STRUCTURAL_PASS = 720
SEMANTIC_PASS = 1
SEMANTIC_DENY = 719
SEMANTIC_HOLD = 0
```

The other 719 mappings are DENY because they contradict the fixture's predeclared exact mapping. This proves the semantic gate is selective rather than permanently closed.

## 13. Test matrix

| Test | Expected |
|---|---|
| generate all 64 B6 states | PASS |
| 64/64 encode-decode roundtrip | PASS |
| Hamming-1 adjacency | PASS |
| polarity normalization invertible | PASS |
| 720 coordinate permutations structurally valid | PASS |
| meet preservation 720/720 | PASS |
| join preservation 720/720 | PASS |
| Hamming preservation 720/720 | PASS |
| AIPRBG -> ESS semantics without axis evidence | HOLD 720/720 |
| positional axis match only | HOLD |
| shared cardinality only | HOLD |
| both systems six-dimensional | HOLD |
| conceptual resemblance only | HOLD |
| 5/6 semantic evidence | HOLD |
| polarity mismatch | DENY |
| unresolved alias conflict | DENY |
| post-hoc selected mapping | DENY |
| unknown/unregistered namespace | HOLD |
| bare `EQ64` semantic reference | DENY_POLICY_BARE_EQ64_FORBIDDEN |
| synthetic exact six-axis evidence | PASS for exactly one mapping |
| other synthetic mappings | DENY_EXACT_MAPPING_CONFLICT |

## 14. Content-addressed receipt

The 720-run produces one canonical top-level receipt.

Minimum schema:

```json
{
  "schema": "EQ64_NAMESPACE_SAFE_CANARY_RECEIPT_V1",
  "source_namespace": "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
  "target_namespace": "ESS_EQ64_6D_KERNEL",
  "permutation_count": 720,
  "structural_pass": 720,
  "semantic_pass": 0,
  "semantic_hold": 720,
  "semantic_deny": 0,
  "unexpected_passes": [],
  "fixture_sha256": "...",
  "engine_sha256": "...",
  "result_sha256": "..."
}
```

The receipt binds exact fixture bytes, engine bytes, canonicalized result bytes, and the run summary by SHA256.

## 15. Build and verification flow

```text
1. Lean build
2. Lean theorem checks
3. Python unit tests
4. 64-state structural tests
5. 720-permutation negative canary
6. synthetic one-positive control
7. receipt-schema validation
8. SHA256 materialization
9. independent readback
```

Any failure yields:

```text
FINAL_STATUS = HOLD
RUNTIME_BIND_CANDIDATE = FALSE
```

No weighted score may override a failed mandatory gate.

## 16. Motorbinding boundary

Reference input contract:

```text
namespace_id
axis_schema
polarity/order contract
evidence map
state vector
```

Reference consumer chain:

```text
source
-> exact namespace/schema validator
-> polarity normalizer
-> structural checker
-> semantic evidence gate
-> namespace-specific encoder
-> receipt generator
-> overclaim guard
```

Persist:

- namespace ID;
- axis-schema digest;
- polarity contract;
- semantic-evidence matrix;
- selected route;
- TRI result;
- claim ceiling;
- receipt digest.

Critical invariant:

```text
STRUCTURAL REUSE MAY CROSS NAMESPACES.
SEMANTIC MEANINGS MAY NOT CROSS NAMESPACES WITHOUT C1-C11 PROOF.
```

## 17. Runtime boundary

Forbidden in this gate:

```text
runtime import
production dependency
pointer mutation
global authority bind
engine auto-registration
active consumer wiring
```

A future runtime architecture must be:

```text
REFERENCE ENGINE
-> CONFORMANCE RECEIPT
-> EXPLICIT RUNTIME BIND GATE
-> ACTIVE ENGINE
```

A passing reference receipt is necessary but not sufficient for runtime admission.

## 18. Overclaim guardrails

Forbidden inferences:

- same cardinality => same semantics;
- Q6 graph isomorphism => semantic identity;
- B6 lattice isomorphism => axis equivalence;
- positional axis match => evidence;
- polarity normalization => domain equivalence;
- Fuller VE => semantic translator;
- AIPRBG audit vector => canonical ESS EQ64 state;
- structural runtime authority => semantic authority;
- high aggregate score => absolute PASS;
- reference-engine PASS => production readiness;
- 720 structural PASS => semantic crosswalk PASS.

## 19. Claim ceiling

Maximum claim after implementation and successful verification:

```text
PASS_REFERENCE_IMPLEMENTATION_CONFORMS_TO_NAMESPACE_SEPARATION_CONTRACT
```

Not established:

- empirical truth;
- physical correctness;
- historical semantic equivalence;
- global authority;
- general runtime admission;
- production readiness.

## 20. Implementation success criteria

```text
LEAN_FORMAL_LAYER = PASS
REFERENCE_ENGINE = PASS
720_NEGATIVE_CANARY = 720/720
SYNTHETIC_POSITIVE = 1/720
SYNTHETIC_CONFLICT_DENY = 719/720
SEMANTIC_LEAKAGE = 0
CONTENT_ADDRESSED_RECEIPT = PASS
RUNTIME_BIND = FALSE
```

## 21. Next transition

After user review and approval of this written specification, create a separate implementation plan preserving:

```text
FORMAL SPEC
-> REFERENCE ENGINE
-> 720 ADVERSARIAL CANARY
-> POSITIVE CONTROL
-> CONTENT-ADDRESSED RECEIPT
```

Only after that phase independently passes may a new `RUNTIME_BIND_GATE` be designed.
