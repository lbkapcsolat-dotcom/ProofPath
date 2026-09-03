import crypto from 'node:crypto';

const GATE = 'ALPHA_GEMINI_ROTATED_KEY_REBIND_VERIFY_V1';
const MODEL = 'gemini-3.7-flash';
const EXPECTED_NEW_KEY_SHA256 = 'cd60b79870298bb4e76cbf823e329d158ce57346e0439f1f5a41897bd8564bf7';

const receipt = {
  gate: GATE,
  status: 'HOLD',
  model: MODEL,
  keyConfigured: Boolean(process.env.GEMINI_API_KEY),
  expectedNewKeyFingerprintMatch: false,
  authenticatedModelSurface: false,
  metadataOnly: true,
  liveInferenceExecuted: false,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false
};

if (!process.env.GEMINI_API_KEY) {
  receipt.status = 'HOLD_GEMINI_API_KEY_NOT_CONFIGURED';
  console.log(JSON.stringify(receipt));
  process.exit(2);
}

const actual = crypto.createHash('sha256').update(process.env.GEMINI_API_KEY).digest('hex');
receipt.expectedNewKeyFingerprintMatch = actual === EXPECTED_NEW_KEY_SHA256;
if (!receipt.expectedNewKeyFingerprintMatch) {
  receipt.status = 'HOLD_GITHUB_SECRET_NOT_BOUND_TO_EXPECTED_NEW_KEY';
  console.log(JSON.stringify(receipt));
  process.exit(2);
}

const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models', {
  headers: { 'x-goog-api-key': process.env.GEMINI_API_KEY }
});
if (!response.ok) {
  receipt.status = `HOLD_GEMINI_MODEL_SURFACE_HTTP_${response.status}`;
  console.log(JSON.stringify(receipt));
  process.exit(2);
}
const payload = await response.json();
receipt.authenticatedModelSurface = (payload.models || [])
  .map(m => String(m.name || '').replace(/^models\//, ''))
  .includes(MODEL);
if (!receipt.authenticatedModelSurface) {
  receipt.status = 'HOLD_GEMINI_3_7_FLASH_NOT_AVAILABLE';
  console.log(JSON.stringify(receipt));
  process.exit(2);
}

receipt.status = 'PASS_NEW_GEMINI_KEY_REBOUND_AND_AUTHENTICATED';
console.log(JSON.stringify(receipt));
