import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { OPENAI_LIVE_MODEL } from './openai-live-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);

const receipt = {
  gate: 'ALPHA_CORPUS_CALLOSUM_OPENAI_MODEL_PREFLIGHT_V1',
  status: 'HOLD',
  packetSha256: bind.packetSha256,
  modelTarget: OPENAI_LIVE_MODEL,
  keyConfigured: Boolean(process.env.OPENAI_API_KEY),
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

if (bind.packetSha256 !== fixture.expectedPacketSha256) {
  receipt.status = 'FAIL_OPENAI_PREFLIGHT_PACKET_IDENTITY_MISMATCH';
  emitReceiptAndExit(receipt);
}

if (!process.env.OPENAI_API_KEY) {
  receipt.status = 'HOLD_OPENAI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS';
  emitReceiptAndExit(receipt);
}

const response = await fetch('https://api.openai.com/v1/models', {
  headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` }
});

if (!response.ok) {
  receipt.status = `HOLD_OPENAI_AUTHENTICATED_MODEL_SURFACE_HTTP_${response.status}`;
  emitReceiptAndExit(receipt);
}

const payload = await response.json();
const ids = (payload.data || []).map(model => String(model.id || ''));
receipt.authenticatedModelSurface = ids.includes(OPENAI_LIVE_MODEL);
if (!receipt.authenticatedModelSurface) {
  receipt.status = 'HOLD_OPENAI_GPT_5_6_SOL_NOT_AVAILABLE_TO_CONFIGURED_KEY';
  emitReceiptAndExit(receipt);
}

receipt.status = 'PASS_AUTH_MODEL_READY';
emitReceiptAndExit(receipt);
