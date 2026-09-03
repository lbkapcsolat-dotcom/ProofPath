import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { buildStructuredClaimPrompt, normalizeStructuredClaimRun, STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const MODEL = 'gemini-3.7-flash';
const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const auth = JSON.parse(fs.readFileSync(new URL('./gemini-live-execution-authorization.json', import.meta.url), 'utf8'));
const security = JSON.parse(fs.readFileSync(new URL('./true-dual-live-security-authorization.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);

const receipt = {
  gate: 'ALPHA_NSH_STRUCTURED_CLAIM_VECTOR_AND_ADJUDICATION_V1',
  status: 'HOLD',
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
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
  receipt.status = 'HOLD_STRUCTURED_CLAIM_MODEL_AUTHORIZATION';
  emitReceiptAndExit(receipt);
}
if (!process.env.GEMINI_API_KEY) {
  receipt.status = 'HOLD_GEMINI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS';
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

const modelsResponse = await fetch('https://generativelanguage.googleapis.com/v1beta/models', {
  headers: { 'x-goog-api-key': process.env.GEMINI_API_KEY }
});
if (!modelsResponse.ok) {
  receipt.status = `HOLD_GEMINI_AUTHENTICATED_MODEL_SURFACE_HTTP_${modelsResponse.status}`;
  emitReceiptAndExit(receipt);
}
const models = await modelsResponse.json();
receipt.authenticatedModelSurface = (models.models || []).map(m => String(m.name || '').replace(/^models\//, '')).includes(MODEL);
if (!receipt.authenticatedModelSurface) {
  receipt.status = 'HOLD_GEMINI_3_7_FLASH_NOT_AVAILABLE_TO_CONFIGURED_KEY';
  emitReceiptAndExit(receipt);
}

const prompt = buildStructuredClaimPrompt('GEMINI', bind);
const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY },
  body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: {
    responseMimeType: 'application/json', responseSchema: { type: 'OBJECT', properties: {
      packetSha256: { type: 'STRING' }, claims: { type: 'ARRAY', items: { type: 'OBJECT', properties: {
        claim_id: { type: 'STRING' }, proposition: { type: 'STRING' }, polarity: { type: 'STRING' }, scope: { type: 'STRING' }, authority_basis: { type: 'STRING' },
        provenance_ids: { type: 'ARRAY', items: { type: 'STRING' } }, uncertainty: { type: 'STRING' }, hold_trigger: { type: 'STRING' }, write_intent: { type: 'BOOLEAN' },
        metric_key: { type: 'STRING' }, metric_value: { type: 'STRING' }, metric_unit: { type: 'STRING' }
      }, required: ['claim_id','proposition','polarity','scope','authority_basis','provenance_ids','uncertainty','hold_trigger','write_intent','metric_key','metric_value','metric_unit'] } }
    }, required: ['packetSha256','claims'] }
  }})
});
receipt.liveInferenceExecuted = true;
if (!response.ok) {
  receipt.status = `HOLD_GEMINI_STRUCTURED_CLAIMS_HTTP_${response.status}`;
  emitReceiptAndExit(receipt);
}
const payload = await response.json();
const text = payload?.candidates?.[0]?.content?.parts?.[0]?.text;
if (!text) {
  receipt.status = 'HOLD_GEMINI_STRUCTURED_CLAIMS_EMPTY';
  emitReceiptAndExit(receipt);
}
let candidate;
try {
  candidate = JSON.parse(text);
} catch {
  receipt.status = 'HOLD_GEMINI_STRUCTURED_CLAIMS_MALFORMED_JSON';
  emitReceiptAndExit(receipt);
}
try {
  receipt.run = normalizeStructuredClaimRun({ consumer: 'GEMINI', ...candidate }, bind);
} catch (error) {
  receipt.status = `HOLD_GEMINI_STRUCTURED_CLAIM_CONTRACT_REJECTED__${String(error?.message || 'unknown').replace(/\s+/g, '_')}`;
  emitReceiptAndExit(receipt);
}
receipt.status = 'PASS_GEMINI_LIVE_STRUCTURED_CLAIM_VECTOR';
emitReceiptAndExit(receipt);
