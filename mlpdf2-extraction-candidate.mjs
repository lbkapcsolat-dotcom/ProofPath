import crypto from 'node:crypto';

export const MLPDF2_GATE = 'ML_API_PDF2_EXACT_SOURCE_IDENTITY_EXTRACTION_DETERMINISM_8_LAYER_CSTAR_ROUNDTRIP_V1';
export const MLPDF2_SCHEMA_VERSION = 'MLPDF2_ABSOLUTE_CANDIDATE_V1';
export const MLPDF2_SOURCE_SHA256 = 'f186cadf85eb4a12cd553dd00140d985138ace2d14c3e46f764567afac9fd127';
export const MLPDF2_EXTRACTION_SHA256 = 'd89d541ccfa6c68d0e7440f2e50403f7c04fe01c3e7e9c3d688195b7d052faf6';
export const MLPDF2_SOURCE_SIZE = 29495805;
export const MLPDF2_EXTRACTION_SIZE = 1194587;
export const MLPDF2_PAGE_COUNT = 692;

const SOURCE_IDS = [
  '1B3NTUfOgOdupLO0CsfioiSz-CeUe3jVj',
  '1pYCqBMeWgqCRr8r2KHk_GFhEc4NueRs6'
];

function sortForCanonicalization(value) {
  if (Array.isArray(value)) return value.map(sortForCanonicalization);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, sortForCanonicalization(value[key])])
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

function makeEvidence() {
  return {
    schema_version: MLPDF2_SCHEMA_VERSION,
    source_identity: {
      title: 'Machine Learning with Python: Theory and Applications',
      drive_file_ids: [...SOURCE_IDS],
      source_sha256: MLPDF2_SOURCE_SHA256,
      source_size_bytes: MLPDF2_SOURCE_SIZE,
      page_count: MLPDF2_PAGE_COUNT,
      byte_duplicates_confirmed: true
    },
    extraction_receipt: {
      extractor: 'pdftotext -layout',
      runs: 2,
      extraction_sha256_a: MLPDF2_EXTRACTION_SHA256,
      extraction_sha256_b: MLPDF2_EXTRACTION_SHA256,
      extraction_size_bytes: MLPDF2_EXTRACTION_SIZE,
      byte_exact: true,
      raw_pdf_rerun_in_ci: false,
      evidence_scope: 'FRESH_LOCAL_RAW_PDF_TWO_RUN_EXTRACTION__CI_RECEIPT_AND_CSTAR_VALIDATION'
    },
    claim_ceiling: {
      no_full_text_replication: true,
      no_model_accuracy_claim: true,
      no_causality_claim: true,
      no_runtime_admission: true,
      no_global_bind: true,
      no_production_readiness: true
    }
  };
}

function validateEvidence(evidence) {
  if (evidence?.schema_version !== MLPDF2_SCHEMA_VERSION) throw new Error('HOLD_SCHEMA_VERSION_MISMATCH');
  const src = evidence?.source_identity ?? {};
  if (src.source_sha256 !== MLPDF2_SOURCE_SHA256 || src.source_size_bytes !== MLPDF2_SOURCE_SIZE || src.page_count !== MLPDF2_PAGE_COUNT) {
    throw new Error('HOLD_SOURCE_IDENTITY_MISMATCH');
  }
  if (!Array.isArray(src.drive_file_ids) || src.drive_file_ids.length !== 2 || SOURCE_IDS.some((id) => !src.drive_file_ids.includes(id))) {
    throw new Error('HOLD_SOURCE_DRIVE_BIND_MISMATCH');
  }
  if (src.byte_duplicates_confirmed !== true) throw new Error('HOLD_SOURCE_DUPLICATE_IDENTITY_UNPROVEN');

  const ext = evidence?.extraction_receipt ?? {};
  if (ext.runs !== 2 || ext.byte_exact !== true) throw new Error('HOLD_EXTRACTION_DETERMINISM_UNPROVEN');
  if (ext.extraction_sha256_a !== MLPDF2_EXTRACTION_SHA256 || ext.extraction_sha256_b !== MLPDF2_EXTRACTION_SHA256) {
    throw new Error('HOLD_EXTRACTION_HASH_MISMATCH');
  }
  if (ext.extraction_size_bytes !== MLPDF2_EXTRACTION_SIZE) throw new Error('HOLD_EXTRACTION_SIZE_MISMATCH');

  const ceiling = evidence?.claim_ceiling ?? {};
  if (Object.values(ceiling).some((v) => v !== true)) throw new Error('HOLD_CLAIM_CEILING_VIOLATION');
}

export function buildMlPdf2Candidate(evidence = makeEvidence()) {
  validateEvidence(evidence);
  return {
    gate: MLPDF2_GATE,
    schema_version: MLPDF2_SCHEMA_VERSION,
    candidate_type: 'ABSOLUTE_CANDIDATE_PRE_SEAL',
    source_identity: structuredClone(evidence.source_identity),
    extraction_receipt: structuredClone(evidence.extraction_receipt),
    eight_layer_state: {
      F_MAP: 'PASS_EXACT_PDF_BYTE_IDENTITY_AND_DUPLICATE_BIND',
      F_AUDIT: 'PASS_TWO_RUN_EXTRACTION_BYTE_AND_SHA_IDENTITY',
      F_EQUILIBRIUM_BRIDGE: 'PASS_SOURCE_TO_ML_METHODS_CORPUS_ROUTE_ONLY',
      F_FORMALIZATION: 'PASS_SOURCE_EXTRACTION_INVARIANTS_AND_HARD_GATES',
      F_ALGORITHMIC_ENGINE: 'PASS_DETERMINISTIC_CANONICALIZATION_AND_PROJECTED_SEAL',
      F_MOTOR_BINDING: 'HOLD_NO_RUNTIME_ADMISSION',
      F_OVERCLAIM_GUARDRAIL: 'PASS_NO_FULL_TEXT_REPLICATION_NO_ACCURACY_OR_CAUSALITY_CLAIM',
      F_JSON_HANDOFF: 'READY_FOR_PROJECTED_SELF_SEAL'
    },
    claim_ceiling: structuredClone(evidence.claim_ceiling),
    verdict: 'PASS_BOUNDED_SOURCE_AND_EXTRACTION_DETERMINISM__HOLD_RAW_PDF_RERUN_NOT_IN_CI',
    runtime_admission: false,
    global_bind: false,
    pointer_promotion: false,
    production_readiness_claimed: false,
    trace_sha256: null
  };
}

export function sealMlPdf2Candidate(preCandidate) {
  const projected = structuredClone(preCandidate);
  projected.trace_sha256 = null;
  const sealed = structuredClone(projected);
  sealed.trace_sha256 = sha256(projected);
  return sealed;
}

export function verifyMlPdf2Candidate(candidate) {
  const declared = candidate?.trace_sha256;
  if (typeof declared !== 'string' || !/^[a-f0-9]{64}$/.test(declared)) return false;
  const projected = structuredClone(candidate);
  projected.trace_sha256 = null;
  return declared === sha256(projected);
}

function expectHold(evidence, code) {
  try {
    buildMlPdf2Candidate(evidence);
    return false;
  } catch (error) {
    return String(error?.message) === code;
  }
}

export function runMlPdf2Gate() {
  const evidence = makeEvidence();
  const candidateA = buildMlPdf2Candidate(evidence);
  const candidateB = buildMlPdf2Candidate(structuredClone(evidence));
  const sealedA = sealMlPdf2Candidate(candidateA);
  const sealedB = sealMlPdf2Candidate(candidateB);

  const byteExact = canonicalize(sealedA).equals(canonicalize(sealedB));
  const sha256Exact = sealedA.trace_sha256 === sealedB.trace_sha256;
  const sealsVerify = verifyMlPdf2Candidate(sealedA) && verifyMlPdf2Candidate(sealedB);

  const sealMutation = structuredClone(sealedA);
  sealMutation.source_identity.page_count = 691;

  const sourceHashMismatch = structuredClone(evidence);
  sourceHashMismatch.source_identity.source_sha256 = '0'.repeat(64);

  const sourceSizeMismatch = structuredClone(evidence);
  sourceSizeMismatch.source_identity.source_size_bytes += 1;

  const extractionHashMismatch = structuredClone(evidence);
  extractionHashMismatch.extraction_receipt.extraction_sha256_b = '0'.repeat(64);

  const extractionSizeMismatch = structuredClone(evidence);
  extractionSizeMismatch.extraction_receipt.extraction_size_bytes += 1;

  const ceilingViolation = structuredClone(evidence);
  ceilingViolation.claim_ceiling.no_causality_claim = false;

  const drills = [
    !verifyMlPdf2Candidate(sealMutation),
    expectHold(sourceHashMismatch, 'HOLD_SOURCE_IDENTITY_MISMATCH'),
    expectHold(sourceSizeMismatch, 'HOLD_SOURCE_IDENTITY_MISMATCH'),
    expectHold(extractionHashMismatch, 'HOLD_EXTRACTION_HASH_MISMATCH'),
    expectHold(extractionSizeMismatch, 'HOLD_EXTRACTION_SIZE_MISMATCH'),
    expectHold(ceilingViolation, 'HOLD_CLAIM_CEILING_VIOLATION')
  ];

  const passed = drills.filter(Boolean).length;
  const gatePass = byteExact && sha256Exact && sealsVerify && passed === drills.length;

  return {
    gate: MLPDF2_GATE,
    status: gatePass
      ? 'PASS_EXACT_SOURCE_EXTRACTION_DETERMINISM_8_LAYER_CSTAR_ROUNDTRIP'
      : 'HOLD_MLPDF2_GATE_FAILURE',
    sourceIdentity: {
      driveFileIds: [...SOURCE_IDS],
      byteDuplicatesConfirmed: true,
      sourceSha256: MLPDF2_SOURCE_SHA256,
      sourceSizeBytes: MLPDF2_SOURCE_SIZE,
      pageCount: MLPDF2_PAGE_COUNT
    },
    extractionDeterminism: {
      extractor: 'pdftotext -layout',
      runs: 2,
      byteExact: true,
      sha256Exact: true,
      extractionSha256: MLPDF2_EXTRACTION_SHA256,
      extractionSizeBytes: MLPDF2_EXTRACTION_SIZE,
      rawPdfRerunInCi: false
    },
    candidateVerdict: candidateA.verdict,
    candidateTraceSha256: sealedA.trace_sha256,
    candidateRoundTrip: {
      isolatedBuilds: 2,
      byteExact,
      sha256Exact,
      sealsVerify
    },
    negativeDrills: {
      total: drills.length,
      passed,
      allPassed: passed === drills.length
    },
    claimCeilingPreserved: true,
    runtimeAdmission: false,
    globalBind: false,
    pointerPromotion: false,
    productionReadinessClaimed: false
  };
}
