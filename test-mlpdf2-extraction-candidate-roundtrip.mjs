import assert from 'node:assert/strict';
import {
  MLPDF2_GATE,
  MLPDF2_SOURCE_SHA256,
  MLPDF2_EXTRACTION_SHA256,
  runMlPdf2Gate
} from './mlpdf2-extraction-candidate.mjs';

assert.equal(MLPDF2_GATE, 'ML_API_PDF2_EXACT_SOURCE_IDENTITY_EXTRACTION_DETERMINISM_8_LAYER_CSTAR_ROUNDTRIP_V1');
assert.equal(MLPDF2_SOURCE_SHA256, 'f186cadf85eb4a12cd553dd00140d985138ace2d14c3e46f764567afac9fd127');
assert.equal(MLPDF2_EXTRACTION_SHA256, 'd89d541ccfa6c68d0e7440f2e50403f7c04fe01c3e7e9c3d688195b7d052faf6');

const receipt = runMlPdf2Gate();
assert.equal(receipt.status, 'PASS_EXACT_SOURCE_EXTRACTION_DETERMINISM_8_LAYER_CSTAR_ROUNDTRIP');
assert.equal(receipt.sourceIdentity.byteDuplicatesConfirmed, true);
assert.equal(receipt.extractionDeterminism.runs, 2);
assert.equal(receipt.extractionDeterminism.byteExact, true);
assert.equal(receipt.extractionDeterminism.sha256Exact, true);
assert.equal(receipt.candidateRoundTrip.isolatedBuilds, 2);
assert.equal(receipt.candidateRoundTrip.byteExact, true);
assert.equal(receipt.candidateRoundTrip.sha256Exact, true);
assert.equal(receipt.candidateRoundTrip.sealsVerify, true);
assert.equal(receipt.negativeDrills.total, 6);
assert.equal(receipt.negativeDrills.passed, 6);
assert.equal(receipt.claimCeilingPreserved, true);
assert.equal(receipt.runtimeAdmission, false);
assert.equal(receipt.globalBind, false);
assert.equal(receipt.pointerPromotion, false);
assert.equal(receipt.productionReadinessClaimed, false);

console.log(JSON.stringify(receipt));
