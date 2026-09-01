import assert from 'node:assert/strict';
import * as engine from './v5-absolute-candidate.mjs';

assert.equal(typeof engine.canonicalize, 'function', 'canonicalize must be implemented');
assert.equal(typeof engine.sealCandidate, 'function', 'sealCandidate must be implemented');
assert.equal(typeof engine.verifyCandidate, 'function', 'verifyCandidate must be implemented');
assert.equal(typeof engine.buildV5Candidate, 'function', 'buildV5Candidate must be implemented');
assert.equal(typeof engine.runV5AbsoluteCandidateGate, 'function', 'runV5AbsoluteCandidateGate must be implemented');

const fixture = {
  schema_version: 'V5_ABSOLUTE_CANDIDATE_V1',
  source_identity: {
    drive_file_id: '1lYFWl92s8r8lQ-sGyAkF16DbOHwKaQK6ukAUz6yRGhk',
    title: 'HDA_EQCTI_V5_20_COUNTRY_BENCHMARK_AND_OOS',
    status_sheet: 'V5_Status',
    source_register_sheet: 'V5_Source_Register'
  },
  source_state: {
    benchmark_country_coverage: 'PASS_20_BENCHMARK_COUNTRIES',
    sequential_oos: 'PASS_BOUNDED_SEQUENTIAL_OOS',
    raw_byte_custody: 'HOLD_RAW_BYTES',
    core_bridge: 'HOLD_ZERO_EXACT_ACTIVE_CORE_FROM_BENCHMARK_PANEL',
    final_ceiling: 'ARCHITECTURE_STRONG__BENCHMARK_VALIDATION_STRONGER__CORE_PANEL_AND_BYTE_CUSTODY_OPEN'
  },
  source_register: [
    ['Eurostat', 'ilc_pw01', '2024 overall life satisfaction, total population age 16+', 'Official Statistics Explained PDF/map', '20-country exact published values'],
    ['World Happiness Report', '2026 Figure 2.1', '2023–2025 average Cantril life evaluation', 'Official WHR report/site', '20-country holdout'],
    ['UNDP HDR', '2025 Table 1', '2023 HDI', 'Official HDR 2025 statistical annex', '20-country holdout'],
    ['Happy Planet Index', '2026 accessible HPI', 'Wellbeing, life expectancy, ecological footprint, HPI score', 'Official accessible HTML', '20-country holdout'],
    ['Social Progress Imperative', '2026 Global SPI', '171 countries, 57 indicators', 'Official public overview', 'Scope only; premium download not used'],
    ['EQCTI internal authority', 'V1.9.99 Indicator Dictionary / Outcome Validation / Wellbeing Benchmarks', 'Active-core vs validation/benchmark role', 'Existing canonical workbook', '99-core bridge authority']
  ],
  claim_ceiling: {
    benchmark_only: true,
    no_causal_interpretation: true,
    no_99_core_promotion: true,
    no_raw_byte_custody_claim: true,
    no_runtime_admission: true,
    no_global_bind: true
  }
};

const candidateA = engine.buildV5Candidate(fixture);
const candidateB = engine.buildV5Candidate(structuredClone(fixture));

assert.equal(candidateA.verdict, 'HOLD_SOURCE_BYTE_CUSTODY_AND_ACTIVE_CORE_OPEN');
assert.equal(candidateB.verdict, candidateA.verdict);
assert.deepEqual(candidateB, candidateA, 'isolated builds must be structurally identical before sealing');

const sealedA = engine.sealCandidate(candidateA);
const sealedB = engine.sealCandidate(candidateB);
assert.equal(engine.verifyCandidate(sealedA), true, 'sealed candidate A must verify');
assert.equal(engine.verifyCandidate(sealedB), true, 'sealed candidate B must verify');
assert.equal(sealedA.trace_sha256, sealedB.trace_sha256, 'isolated seals must have identical SHA256');
assert.deepEqual(engine.canonicalize(sealedA), engine.canonicalize(sealedB), 'isolated canonical bytes must match exactly');

// Negative drill 1: payload mutation must break the seal.
const payloadMutation = structuredClone(sealedA);
payloadMutation.source_state.sequential_oos = 'MUTATED';
assert.equal(engine.verifyCandidate(payloadMutation), false, 'payload mutation must invalidate seal');

// Negative drill 2: declared trace mutation must break the seal.
const traceMutation = structuredClone(sealedA);
traceMutation.trace_sha256 = '0'.repeat(64);
assert.equal(engine.verifyCandidate(traceMutation), false, 'trace mutation must invalidate seal');

// Negative drill 3: schema drift must fail closed.
const schemaDrift = structuredClone(fixture);
schemaDrift.schema_version = 'V5_ABSOLUTE_CANDIDATE_V0';
assert.throws(() => engine.buildV5Candidate(schemaDrift), /HOLD_SCHEMA_VERSION_MISMATCH/);

// Negative drill 4: exact source identity mismatch must fail closed.
const sourceMismatch = structuredClone(fixture);
sourceMismatch.source_identity.drive_file_id = 'WRONG';
assert.throws(() => engine.buildV5Candidate(sourceMismatch), /HOLD_SOURCE_IDENTITY_MISMATCH/);

// Negative drill 5: weakening a mandatory claim ceiling must fail closed.
const ceilingViolation = structuredClone(fixture);
ceilingViolation.claim_ceiling.no_causal_interpretation = false;
assert.throws(() => engine.buildV5Candidate(ceilingViolation), /HOLD_CLAIM_CEILING_VIOLATION/);

// Negative drill 6: benchmark-to-core promotion must fail closed.
const corePromotion = structuredClone(fixture);
corePromotion.claim_ceiling.no_99_core_promotion = false;
assert.throws(() => engine.buildV5Candidate(corePromotion), /HOLD_CLAIM_CEILING_VIOLATION/);

const receipt = engine.runV5AbsoluteCandidateGate(fixture);
assert.equal(receipt.gate, 'V5_BENCHMARK_ABSOLUTE_CANDIDATE_DETERMINISTIC_ROUNDTRIP_AND_NEGATIVE_DRILL_V1');
assert.equal(receipt.status, 'PASS_DETERMINISTIC_ROUNDTRIP_AND_NEGATIVE_DRILLS');
assert.equal(receipt.candidateVerdict, 'HOLD_SOURCE_BYTE_CUSTODY_AND_ACTIVE_CORE_OPEN');
assert.equal(receipt.roundTrip.byteExact, true);
assert.equal(receipt.roundTrip.sha256Exact, true);
assert.equal(receipt.negativeDrills.total, 6);
assert.equal(receipt.negativeDrills.passed, 6);
assert.equal(receipt.claimCeilingPreserved, true);
assert.equal(receipt.runtimeAdmission, false);
assert.equal(receipt.globalBind, false);

console.log(JSON.stringify(receipt));
