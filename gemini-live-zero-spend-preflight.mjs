import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);
if (bind.packetSha256 !== fixture.expectedPacketSha256) {
  throw new Error('shared packet hash mismatch');
}

const result = {
  gate: 'GEMINI_LIVE_SAME_PACKET_EXECUTION_RECEIPT_V1',
  packetSha256: bind.packetSha256,
  systemAuthority: `${bind.authority.systemMaster}/${bind.authority.systemBoot}`,
  corpusRouter: `${bind.authority.corpusMaster}/${bind.authority.corpusBoot}`,
  zeroSpendPolicy: true,
  modelTarget: 'gemini-3.7-flash',
  keyConfigured: Boolean(process.env.GEMINI_API_KEY),
  authenticatedModelSurface: false,
  liveInferenceExecuted: false,
  status: 'HOLD'
};

if (!process.env.GEMINI_API_KEY) {
  result.status = 'HOLD_GEMINI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS';
  emitReceiptAndExit(result);
}

const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models', {
  headers: { 'x-goog-api-key': process.env.GEMINI_API_KEY }
});
if (!response.ok) {
  result.status = `HOLD_GEMINI_AUTHENTICATED_MODEL_SURFACE_HTTP_${response.status}`;
  emitReceiptAndExit(result);
}
const data = await response.json();
const ids = (data.models || []).map(m => String(m.name || '').replace(/^models\//, ''));
result.authenticatedModelSurface = ids.includes(result.modelTarget);
if (!result.authenticatedModelSurface) {
  result.status = 'HOLD_GEMINI_3_7_FLASH_NOT_AVAILABLE_TO_CONFIGURED_KEY';
  emitReceiptAndExit(result);
}

result.status = 'PASS_AUTH_MODEL_READY';
emitReceiptAndExit(result);
