import fs from 'node:fs';
import {
  buildCorpusCallosumReadOnlyBind,
  buildIndependentReasoningPrompt,
  normalizeReasoningRun
} from './corpus-callosum-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const MODEL = 'gemini-3.7-flash';
const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const auth = JSON.parse(fs.readFileSync(new URL('./gemini-live-execution-authorization.json', import.meta.url), 'utf8'));
const security = JSON.parse(fs.readFileSync(new URL('./true-dual-live-security-authorization.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);

const receipt = {
  gate: 'GEMINI_LIVE_SAME_PACKET_EXECUTION_RECEIPT_V1',
  status: 'HOLD',
  packetSha256: bind.packetSha256,
  systemAuthority: `${bind.authority.systemMaster}/${bind.authority.systemBoot}`,
  corpusRouter: `${bind.authority.corpusMaster}/${bind.authority.corpusBoot}`,
  model: MODEL,
  authorizationGate: auth.gate,
  authorizationBasis: auth.authorizationBasis,
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
if (auth.modelTarget !== MODEL) {
  receipt.status = 'HOLD_MODEL_AUTHORIZATION_MISMATCH';
  emitReceiptAndExit(receipt);
}
if (auth.authorized !== true) {
  receipt.status = 'HOLD_USER_FREE_TIER_READBACK_REQUIRED';
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
const available = (models.models || []).map(m => String(m.name || '').replace(/^models\//, ''));
receipt.authenticatedModelSurface = available.includes(MODEL);
if (!receipt.authenticatedModelSurface) {
  receipt.status = 'HOLD_GEMINI_3_7_FLASH_NOT_AVAILABLE_TO_CONFIGURED_KEY';
  emitReceiptAndExit(receipt);
}

const prompt = buildIndependentReasoningPrompt('GEMINI', bind);
const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-goog-api-key': process.env.GEMINI_API_KEY
  },
  body: JSON.stringify({
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: {
      responseMimeType: 'application/json',
      responseSchema: {
        type: 'OBJECT',
        properties: {
          conclusion: { type: 'STRING' },
          reasoning: { type: 'STRING' },
          provenanceIds: { type: 'ARRAY', items: { type: 'STRING' } },
          uncertainties: { type: 'ARRAY', items: { type: 'STRING' } }
        },
        required: ['conclusion', 'reasoning', 'provenanceIds', 'uncertainties']
      }
    }
  })
});
receipt.liveInferenceExecuted = true;
if (!response.ok) {
  receipt.status = `HOLD_GEMINI_LIVE_HTTP_${response.status}`;
  emitReceiptAndExit(receipt);
}
const payload = await response.json();
const text = payload?.candidates?.[0]?.content?.parts?.[0]?.text;
if (!text) {
  receipt.status = 'HOLD_GEMINI_LIVE_EMPTY_REASONING';
  emitReceiptAndExit(receipt);
}
let candidate;
try {
  candidate = JSON.parse(text);
} catch {
  receipt.status = 'HOLD_GEMINI_LIVE_MALFORMED_JSON';
  emitReceiptAndExit(receipt);
}

try {
  receipt.run = normalizeReasoningRun({
    consumer: 'GEMINI',
    packetSha256: bind.packetSha256,
    ...candidate
  }, bind);
} catch (error) {
  receipt.status = `HOLD_GEMINI_REASONING_CONTRACT_REJECTED__${String(error?.message || 'unknown').replace(/\s+/g, '_')}`;
  emitReceiptAndExit(receipt);
}

receipt.status = 'PASS_GEMINI_LIVE_SAME_PACKET_EXECUTION';
emitReceiptAndExit(receipt);
