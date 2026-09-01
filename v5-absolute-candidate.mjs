import crypto from 'node:crypto';

export const V5_ABSOLUTE_CANDIDATE_GATE = 'V5_BENCHMARK_ABSOLUTE_CANDIDATE_DETERMINISTIC_ROUNDTRIP_AND_NEGATIVE_DRILL_V1';
export const V5_SCHEMA_VERSION = 'V5_ABSOLUTE_CANDIDATE_V1';
export const V5_SOURCE_ID = '1lYFWl92s8r8lQ-sGyAkF16DbOHwKaQK6ukAUz6yRGhk';
export const V5_SOURCE_TITLE = 'HDA_EQCTI_V5_20_COUNTRY_BENCHMARK_AND_OOS';

function sortForCanonicalization(value) {
  if (Array.isArray(value)) return value.map(sortForCanonicalization);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, sortForCanonicalization(value[key])])
    );
  }
  return value;
}

export function canonicalize(value) {
  return Buffer.from(JSON.stringify(sortForCanonicalization(value)), 'utf8');
}

function sha256(value) {
  return crypto.createHash('sha256').update(canonicalize(value)).digest('hex');
}

function validateFixture(fixture) {
  if (fixture?.schema_version !== V5_SCHEMA_VERSION) {
    throw new Error('HOLD_SCHEMA_VERSION_MISMATCH');
  }

  const source = fixture?.source_identity ?? {};
  if (
    source.drive_file_id !== V5_SOURCE_ID ||
    source.title !== V5_SOURCE_TITLE ||
    source.status_sheet !== 'V5_Status' ||
    source.source_register_sheet !== 'V5_Source_Register'
  ) {
    throw new Error('HOLD_SOURCE_IDENTITY_MISMATCH');
  }

  const ceiling = fixture?.claim_ceiling ?? {};
  const mandatoryCeilingFlags = [
    'benchmark_only',
    'no_causal_interpretation',
    'no_99_core_promotion',
    'no_raw_byte_custody_claim',
    'no_runtime_admission',
    'no_global_bind'
  ];
  if (mandatoryCeilingFlags.some((flag) => ceiling[flag] !== true)) {
    throw new Error('HOLD_CLAIM_CEILING_VIOLATION');
  }

  if (!Array.isArray(fixture?.source_register) || fixture.source_register.length === 0) {
    throw new Error('HOLD_SOURCE_REGISTER_MISSING');
  }
  if (!fixture?.source_state || typeof fixture.source_state !== 'object') {
    throw new Error('HOLD_SOURCE_STATE_MISSING');
  }
}

export function buildV5Candidate(fixture) {
  validateFixture(fixture);

  const sourceState = structuredClone(fixture.source_state);
  const rawBytesOpen = sourceState.raw_byte_custody === 'HOLD_RAW_BYTES';
  const activeCoreOpen = sourceState.core_bridge === 'HOLD_ZERO_EXACT_ACTIVE_CORE_FROM_BENCHMARK_PANEL';

  let verdict = 'PASS_BOUNDED_V5_BENCHMARK_CANDIDATE';
  if (rawBytesOpen && activeCoreOpen) {
    verdict = 'HOLD_SOURCE_BYTE_CUSTODY_AND_ACTIVE_CORE_OPEN';
  } else if (rawBytesOpen) {
    verdict = 'HOLD_SOURCE_BYTE_CUSTODY_OPEN';
  } else if (activeCoreOpen) {
    verdict = 'HOLD_ACTIVE_CORE_OPEN';
  }

  return {
    gate: V5_ABSOLUTE_CANDIDATE_GATE,
    schema_version: V5_SCHEMA_VERSION,
    candidate_type: 'ABSOLUTE_CANDIDATE_PRE_SEAL',
    source_identity: structuredClone(fixture.source_identity),
    source_state: sourceState,
    source_register: structuredClone(fixture.source_register),
    eight_layer_state: {
      F_MAP: 'PASS_EXACT_V5_STATUS_AND_SOURCE_REGISTER_BIND',
      F_AUDIT: rawBytesOpen ? 'HOLD_RAW_BYTE_CUSTODY_OPEN' : 'PASS_SOURCE_CUSTODY',
      F_EQUILIBRIUM_BRIDGE: activeCoreOpen ? 'HOLD_ACTIVE_CORE_BRIDGE_OPEN' : 'PASS_ACTIVE_CORE_BRIDGE',
      F_FORMALIZATION: 'PASS_FAIL_CLOSED_STATE_AND_CLAIM_BOUNDARY',
      F_ALGORITHMIC_ENGINE: 'PASS_DETERMINISTIC_CANONICALIZATION_AND_PROJECTED_SEAL',
      F_MOTOR_BINDING: 'HOLD_NO_RUNTIME_ADMISSION',
      F_OVERCLAIM_GUARDRAIL: 'PASS_CLAIM_CEILING_PRESERVED',
      F_JSON_HANDOFF: 'READY_FOR_PROJECTED_SELF_SEAL'
    },
    claim_ceiling: structuredClone(fixture.claim_ceiling),
    verdict,
    runtime_admission: false,
    global_bind: false,
    pointer_promotion: false,
    authority_mutation: false,
    trace_sha256: null
  };
}

export function sealCandidate(preCandidate) {
  const projected = structuredClone(preCandidate);
  projected.trace_sha256 = null;

  const sealed = structuredClone(projected);
  sealed.trace_sha256 = sha256(projected);
  return sealed;
}

export function verifyCandidate(candidate) {
  const declared = candidate?.trace_sha256;
  if (typeof declared !== 'string' || !/^[a-f0-9]{64}$/.test(declared)) return false;

  const projected = structuredClone(candidate);
  projected.trace_sha256 = null;
  return declared === sha256(projected);
}

function expectBuildHold(fixture, expectedCode) {
  try {
    buildV5Candidate(fixture);
    return false;
  } catch (error) {
    return String(error?.message) === expectedCode;
  }
}

export function runV5AbsoluteCandidateGate(fixture) {
  const candidateA = buildV5Candidate(fixture);
  const candidateB = buildV5Candidate(structuredClone(fixture));
  const sealedA = sealCandidate(candidateA);
  const sealedB = sealCandidate(candidateB);

  const byteExact = canonicalize(sealedA).equals(canonicalize(sealedB));
  const sha256Exact = sealedA.trace_sha256 === sealedB.trace_sha256;
  const sealsVerify = verifyCandidate(sealedA) && verifyCandidate(sealedB);

  const payloadMutation = structuredClone(sealedA);
  payloadMutation.source_state.sequential_oos = 'MUTATED';

  const traceMutation = structuredClone(sealedA);
  traceMutation.trace_sha256 = '0'.repeat(64);

  const schemaDrift = structuredClone(fixture);
  schemaDrift.schema_version = 'V5_ABSOLUTE_CANDIDATE_V0';

  const sourceMismatch = structuredClone(fixture);
  sourceMismatch.source_identity.drive_file_id = 'WRONG';

  const ceilingViolation = structuredClone(fixture);
  ceilingViolation.claim_ceiling.no_causal_interpretation = false;

  const corePromotion = structuredClone(fixture);
  corePromotion.claim_ceiling.no_99_core_promotion = false;

  const drillResults = [
    !verifyCandidate(payloadMutation),
    !verifyCandidate(traceMutation),
    expectBuildHold(schemaDrift, 'HOLD_SCHEMA_VERSION_MISMATCH'),
    expectBuildHold(sourceMismatch, 'HOLD_SOURCE_IDENTITY_MISMATCH'),
    expectBuildHold(ceilingViolation, 'HOLD_CLAIM_CEILING_VIOLATION'),
    expectBuildHold(corePromotion, 'HOLD_CLAIM_CEILING_VIOLATION')
  ];

  const passed = drillResults.filter(Boolean).length;
  const claimCeilingPreserved = Object.values(fixture.claim_ceiling).every((value) => value === true);
  const gatePass = byteExact && sha256Exact && sealsVerify && passed === drillResults.length && claimCeilingPreserved;

  return {
    gate: V5_ABSOLUTE_CANDIDATE_GATE,
    status: gatePass
      ? 'PASS_DETERMINISTIC_ROUNDTRIP_AND_NEGATIVE_DRILLS'
      : 'HOLD_DETERMINISTIC_ROUNDTRIP_OR_NEGATIVE_DRILL_FAILURE',
    sourceIdentity: structuredClone(fixture.source_identity),
    candidateVerdict: candidateA.verdict,
    candidateTraceSha256: sealedA.trace_sha256,
    roundTrip: {
      isolatedBuilds: 2,
      byteExact,
      sha256Exact,
      sealsVerify
    },
    negativeDrills: {
      total: drillResults.length,
      passed,
      allPassed: passed === drillResults.length
    },
    claimCeilingPreserved,
    runtimeAdmission: false,
    globalBind: false,
    pointerPromotion: false,
    authorityMutation: false,
    productionReadinessClaimed: false
  };
}
