import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { buildDualLiveStructuredClaimPrompt, normalizeDualLiveClaimRun, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const MODEL = 'gemini-3.7-flash';
const GATE = 'ALPHA_CORPUS_CALLOSUM_SECURITY_AND_TRUE_DUAL_LIVE_CLOSE_V1';
const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const auth = JSON.parse(fs.readFileSync(new URL('./gemini-live-execution-authorization.json', import.meta.url), 'utf8'));
const security = JSON.parse(fs.readFileSync(new URL('./true-dual-live-security-authorization.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);

const receipt = {
  gate: GATE,
  status: 'HOLD',
  provider: 'Google',
  providerSurface: 'Generative Language API',
  executionMode: 'LIVE_GEMINI_API',
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
  claimOntology: DUAL_LIVE_CLAIM_ONTOLOGY_ID,
  packetSha256: bind.packetSha256,
  model: MODEL,
  freeTierAuthorized: auth.authorized === true,
  keyConfigured: Boolean(process.env.GEMINI_API_KEY),
  credentialRotationRequired: security.geminiCredentialRotationRequired === true,
  credentialRotationProven: security.geminiCredentialRotationProven === true,
  oldCredentialRevoked: security.oldGeminiCredentialRevoked === true,
  newCredentialReboundToGitHubSecret: security.newGeminiCredentialReboundToGitHubSecret === true,
  authenticatedModelSurface: false,
  liveInferenceExecuted: false,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false
};

if (bind.packetSha256 !== auth.packetSha256 || bind.packetSha256 !== fixture.expectedPacketSha256 || bind.packetSha256 !== security.packetSha256) {
  receipt.status = 'FAIL_GEMINI_SHARED_PACKET_IDENTITY_MISMATCH';
  emitReceiptAndExit(receipt);
}
if (auth.modelTarget !== MODEL || auth.authorized !== true) {
  receipt.status = 'HOLD_GEMINI_MODEL_AUTHORIZATION';
  emitReceiptAndExit(receipt);
}
if (security.geminiCredentialRotationRequired === true && (
  security.geminiCredentialRotationProven !== true ||
  security.oldGeminiCredentialRevoked !== true ||
  security.newGeminiCredentialReboundToGitHubSecret !== true
)) {
  receipt.status = 'HOLD_GEMINI_CREDENTIAL_ROTATION_NOT_PROVEN';
  emitReceiptAndExit(receipt);
}
if (!process.env.GEMINI_API_KEY) {
  receipt.status = 'HOLD_GEMINI_API_KEY_NOT_CONFIGURED';
  emitReceiptAndExit(receipt);
}

const modelsResponse = await fetch('https://generativelanguage.googleapis.com/v1beta/models', {
  headers: { 'x-goog-api-key': process.env.GEMINI_API_KEY }
});
if (!modelsResponse.ok) {
  receipt.status = `HOLD_GEMINI_MODEL_SURFACE_HTTP_${modelsResponse.status}`;
  emitReceiptAndExit(receipt);
}
const models = await modelsResponse.json();
receipt.authenticatedModelSurface = (models.models || []).map(m => String(m.name || '').replace(/^models\//, '')).includes(MODEL);
if (!receipt.authenticatedModelSurface) {
  receipt.status = 'HOLD_GEMINI_MODEL_NOT_AVAILABLE';
  emitReceiptAndExit(receipt);
}

const prompt = buildDualLiveStructuredClaimPrompt('GEMINI', bind);
const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-goog-api-key': process.env.GEMINI_API_KEY
  },
  body: JSON.stringify({
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: { responseMimeType: 'application/json' }
  })
});
receipt.liveInferenceExecuted = true;
if (!response.ok) {
  receipt.status = `HOLD_GEMINI_DUAL_LIVE_HTTP_${response.status}`;
  emitReceiptAndExit(receipt);
}
const payload = await response.json();
const text = payload?.candidates?.[0]?.content?.parts?.[0]?.text;
if (!text) {
  receipt.status = 'HOLD_GEMINI_DUAL_LIVE_EMPTY';
  emitReceiptAndExit(receipt);
}
let candidate;
try {
  candidate = JSON.parse(text);
} catch {
  receipt.status = 'HOLD_GEMINI_DUAL_LIVE_MALFORMED_JSON';
  emitReceiptAndExit(receipt);
}
try {
  receipt.run = normalizeDualLiveClaimRun({ consumer: 'GEMINI', ...candidate }, bind);
} catch (error) {
  receipt.status = `HOLD_GEMINI_DUAL_LIVE_CONTRACT_REJECTED__${String(error?.message || 'unknown').replace(/\s+/g, '_')}`;
  emitReceiptAndExit(receipt);
}
receipt.status = 'PASS_GEMINI_DUAL_LIVE_STRUCTURED_CLAIM_VECTOR';
emitReceiptAndExit(receipt);
