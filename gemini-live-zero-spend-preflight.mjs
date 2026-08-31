import fs from 'node:fs';
import {
  buildCorpusCallosumReadOnlyBind,
  buildIndependentReasoningPrompt
} from './corpus-callosum-contract.mjs';

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
  zeroSpend: true,
  modelTarget: 'gemini-3.7-flash',
  keyConfigured: Boolean(process.env.GEMINI_API_KEY),
  authenticatedModelSurface: false,
  liveInferenceExecuted: false,
  verdict: 'HOLD'
};

if (!process.env.GEMINI_API_KEY) {
  result.verdict = 'HOLD_GEMINI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS';
  console.log(JSON.stringify(result));
  process.exit(0);
}

// Metadata-only authentication/model discovery. This intentionally performs no
// generative inference and therefore cannot consume model tokens or paid credits.
const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models', {
  headers: { 'x-goog-api-key': process.env.GEMINI_API_KEY }
});
if (!response.ok) {
  result.verdict = `HOLD_GEMINI_AUTHENTICATED_MODEL_SURFACE_HTTP_${response.status}`;
  console.log(JSON.stringify(result));
  process.exit(0);
}
const data = await response.json();
const ids = (data.models || []).map(m => String(m.name || '').replace(/^models\//, ''));
result.authenticatedModelSurface = ids.includes(result.modelTarget);
if (!result.authenticatedModelSurface) {
  result.verdict = 'HOLD_GEMINI_3_7_FLASH_NOT_AVAILABLE_TO_CONFIGURED_KEY';
  console.log(JSON.stringify(result));
  process.exit(0);
}

// Constructing the exact prompt is safe; sending it is deliberately withheld
// until a no-charge execution surface is proven rather than merely assumed.
const prompt = buildIndependentReasoningPrompt('GEMINI', bind);
result.promptPacketBound = prompt.includes(bind.packetSha256);
result.verdict = 'HOLD_ZERO_SPEND_LIVE_INFERENCE_SURFACE_NOT_PROVEN';
console.log(JSON.stringify(result));
