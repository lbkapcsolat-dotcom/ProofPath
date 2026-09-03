import assert from 'node:assert/strict';
import { DUAL_LIVE_CLAIM_ONTOLOGY } from './dual-live-structured-claim-contract.mjs';
import {
  OPENAI_LIVE_MODEL,
  verifyOpenAiLiveStructuredReceipt
} from './openai-live-contract.mjs';

const bind = {
  gate: 'CORPUS_COLOSSUM_GEMINI_READ_ONLY_BIND_V1',
  mode: 'READ_ONLY',
  writeAuthority: false,
  packetSha256: 'a'.repeat(64),
  sources: [{ id: 's1' }],
  question: 'q'
};
const claim = (claim_id) => ({
  claim_id,
  proposition: `${claim_id} proposition`,
  polarity: 'AFFIRM',
  scope: 'system',
  authority_basis: 'A3460/BOOT2106',
  provenance_ids: ['s1'],
  uncertainty: '',
  hold_trigger: '',
  write_intent: false,
  metric_key: '',
  metric_value: '',
  metric_unit: ''
});
const claims = DUAL_LIVE_CLAIM_ONTOLOGY.map(x => claim(x.claim_id));

assert.equal(OPENAI_LIVE_MODEL, 'gpt-5.6-sol');

const good = {
  status: 'PASS_GPT_LIVE_OPENAI_API_STRUCTURED_CLAIM_VECTOR',
  provider: 'OpenAI',
  providerSurface: 'Responses API',
  executionMode: 'LIVE_OPENAI_API',
  model: OPENAI_LIVE_MODEL,
  packetSha256: bind.packetSha256,
  claimSchema: 'ALPHA_NSH_STRUCTURED_CLAIM_VECTOR_V1',
  claimOntology: 'ALPHA_NSH_DUAL_LIVE_CLAIM_ONTOLOGY_V1',
  liveInferenceExecuted: true,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false,
  run: { consumer: 'GPT', packetSha256: bind.packetSha256, claims }
};
const normalized = verifyOpenAiLiveStructuredReceipt(good, bind);
assert.equal(normalized.consumer, 'GPT');
assert.equal(normalized.claimOntology, 'ALPHA_NSH_DUAL_LIVE_CLAIM_ONTOLOGY_V1');
assert.equal(normalized.claims.length, DUAL_LIVE_CLAIM_ONTOLOGY.length);

assert.throws(() => verifyOpenAiLiveStructuredReceipt({
  ...good,
  providerSurface: 'ChatGPT',
  executionMode: 'LIVE_CHATGPT_SESSION_NOT_API_PROVIDER_RECEIPT'
}, bind), /Responses API/i);

assert.throws(() => verifyOpenAiLiveStructuredReceipt({ ...good, liveInferenceExecuted: false }, bind), /live inference/i);
assert.throws(() => verifyOpenAiLiveStructuredReceipt({ ...good, packetSha256: 'b'.repeat(64) }, bind), /packet/i);

console.log('PASS OpenAI true-live structured provider contract');
