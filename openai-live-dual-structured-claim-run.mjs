import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import {
  buildDualLiveStructuredClaimPrompt,
  normalizeDualLiveClaimRun,
  DUAL_LIVE_CLAIM_ONTOLOGY,
  DUAL_LIVE_CLAIM_ONTOLOGY_ID
} from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';
import {
  OPENAI_LIVE_MODEL,
  OPENAI_PROVIDER,
  OPENAI_PROVIDER_SURFACE,
  OPENAI_EXECUTION_MODE,
  OPENAI_LIVE_PASS
} from './openai-live-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const auth = JSON.parse(fs.readFileSync(new URL('./openai-live-execution-authorization.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);

const receipt = {
  gate: 'ALPHA_CORPUS_CALLOSUM_SECURITY_AND_TRUE_DUAL_LIVE_CLOSE_V1',
  status: 'HOLD',
  provider: OPENAI_PROVIDER,
  providerSurface: OPENAI_PROVIDER_SURFACE,
  executionMode: OPENAI_EXECUTION_MODE,
  model: OPENAI_LIVE_MODEL,
  packetSha256: bind.packetSha256,
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
  claimOntology: DUAL_LIVE_CLAIM_ONTOLOGY_ID,
  keyConfigured: Boolean(process.env.OPENAI_API_KEY),
  zeroSpendRequired: auth.zeroSpendRequired === true,
  zeroSpendProven: auth.zeroSpendProven === true,
  liveInferenceAuthorized: auth.liveInferenceAuthorized === true,
  liveInferenceExecuted: false,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false
};

if (bind.packetSha256 !== fixture.expectedPacketSha256 || bind.packetSha256 !== auth.packetSha256) {
  receipt.status = 'FAIL_OPENAI_SHARED_PACKET_IDENTITY_MISMATCH';
  emitReceiptAndExit(receipt);
}
if (auth.modelTarget !== OPENAI_LIVE_MODEL || auth.apiSurface !== OPENAI_PROVIDER_SURFACE) {
  receipt.status = 'FAIL_OPENAI_EXECUTION_AUTHORIZATION_MISMATCH';
  emitReceiptAndExit(receipt);
}
if (!process.env.OPENAI_API_KEY) {
  receipt.status = 'HOLD_OPENAI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS';
  emitReceiptAndExit(receipt);
}
if (auth.zeroSpendRequired === true && (auth.zeroSpendProven !== true || auth.liveInferenceAuthorized !== true)) {
  receipt.status = 'HOLD_OPENAI_ZERO_SPEND_LIVE_INFERENCE_NOT_PROVEN';
  emitReceiptAndExit(receipt);
}

const prompt = buildDualLiveStructuredClaimPrompt('GPT', bind);
const claimIds = DUAL_LIVE_CLAIM_ONTOLOGY.map(x => x.claim_id);
const schema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    packetSha256: { type: 'string' },
    claims: {
      type: 'array',
      minItems: claimIds.length,
      maxItems: claimIds.length,
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          claim_id: { type: 'string', enum: claimIds },
          proposition: { type: 'string' },
          polarity: { type: 'string', enum: ['AFFIRM', 'DENY', 'UNCERTAIN'] },
          scope: { type: 'string' },
          authority_basis: { type: 'string' },
          provenance_ids: { type: 'array', items: { type: 'string' } },
          uncertainty: { type: 'string' },
          hold_trigger: { type: 'string' },
          write_intent: { type: 'boolean', enum: [false] },
          metric_key: { type: 'string' },
          metric_value: { type: 'string' },
          metric_unit: { type: 'string' }
        },
        required: [
          'claim_id', 'proposition', 'polarity', 'scope', 'authority_basis',
          'provenance_ids', 'uncertainty', 'hold_trigger', 'write_intent',
          'metric_key', 'metric_value', 'metric_unit'
        ]
      }
    }
  },
  required: ['packetSha256', 'claims']
};

const response = await fetch('https://api.openai.com/v1/responses', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${process.env.OPENAI_API_KEY}`
  },
  body: JSON.stringify({
    model: OPENAI_LIVE_MODEL,
    input: prompt,
    store: false,
    reasoning: { effort: 'medium' },
    text: {
      format: {
        type: 'json_schema',
        name: 'corpus_callosum_dual_live_claims',
        strict: true,
        schema
      }
    }
  })
});
receipt.liveInferenceExecuted = true;

if (!response.ok) {
  receipt.status = `HOLD_OPENAI_LIVE_HTTP_${response.status}`;
  emitReceiptAndExit(receipt);
}

const payload = await response.json();
const texts = [];
for (const item of payload.output || []) {
  if (item?.type !== 'message') continue;
  for (const part of item.content || []) {
    if (part?.type === 'output_text' && typeof part.text === 'string') texts.push(part.text);
  }
}
const text = texts.join('').trim();
if (!text) {
  receipt.status = 'HOLD_OPENAI_LIVE_EMPTY_STRUCTURED_OUTPUT';
  emitReceiptAndExit(receipt);
}

let candidate;
try {
  candidate = JSON.parse(text);
} catch {
  receipt.status = 'HOLD_OPENAI_LIVE_MALFORMED_JSON';
  emitReceiptAndExit(receipt);
}

try {
  receipt.run = normalizeDualLiveClaimRun({
    consumer: 'GPT',
    packetSha256: candidate.packetSha256,
    claims: candidate.claims
  }, bind);
} catch (error) {
  receipt.status = `HOLD_OPENAI_STRUCTURED_CLAIM_CONTRACT_REJECTED__${String(error?.message || 'unknown').replace(/\s+/g, '_')}`;
  emitReceiptAndExit(receipt);
}

receipt.providerResponseId = payload.id || null;
receipt.usage = payload.usage || null;
receipt.status = OPENAI_LIVE_PASS;
emitReceiptAndExit(receipt);
