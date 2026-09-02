import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { DUAL_LIVE_CLAIM_ONTOLOGY, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';
import { OPENAI_LIVE_MODEL, OPENAI_LIVE_PASS } from './openai-live-contract.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);
const prov = bind.sources.map(s => s.id);
const claims = DUAL_LIVE_CLAIM_ONTOLOGY.map(({ claim_id }) => ({
  claim_id,
  proposition: `${claim_id} canonical proposition`,
  polarity: claim_id === 'FULL_RAW_CORPUS_BYTE_CUSTODY' || claim_id === 'PRODUCTION_RUNTIME_ADMISSION' ? 'DENY' : 'AFFIRM',
  scope: 'canonical',
  authority_basis: 'A3460/BOOT2106+A3449/BOOT2095',
  provenance_ids: prov,
  uncertainty: '',
  hold_trigger: '',
  write_intent: false,
  metric_key: '',
  metric_value: '',
  metric_unit: ''
}));

const openai = {
  status: OPENAI_LIVE_PASS,
  provider: 'OpenAI',
  providerSurface: 'Responses API',
  executionMode: 'LIVE_OPENAI_API',
  model: OPENAI_LIVE_MODEL,
  packetSha256: bind.packetSha256,
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
  claimOntology: DUAL_LIVE_CLAIM_ONTOLOGY_ID,
  liveInferenceExecuted: true,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false,
  run: { consumer: 'GPT', packetSha256: bind.packetSha256, claims }
};
const gemini = {
  status: 'PASS_GEMINI_DUAL_LIVE_STRUCTURED_CLAIM_VECTOR',
  provider: 'Google',
  providerSurface: 'Generative Language API',
  executionMode: 'LIVE_GEMINI_API',
  model: 'gemini-3.7-flash',
  packetSha256: bind.packetSha256,
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
  claimOntology: DUAL_LIVE_CLAIM_ONTOLOGY_ID,
  liveInferenceExecuted: true,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false,
  run: { consumer: 'GEMINI', packetSha256: bind.packetSha256, claims }
};

const openaiFile = 'openai-live-dual-structured-claim-receipt.test.json';
const geminiFile = 'gemini-live-dual-structured-claim-receipt.test.json';
fs.writeFileSync(openaiFile, JSON.stringify(openai));
fs.writeFileSync(geminiFile, JSON.stringify(gemini));
try {
  const run = spawnSync(process.execPath, [
    'compute-dual-live-structured-adjudication-receipt.mjs',
    openaiFile,
    geminiFile
  ], { encoding: 'utf8' });
  assert.equal(run.status, 0);
  assert.equal(run.stderr, '');
  const receipt = JSON.parse(run.stdout.trim());
  assert.equal(receipt.status, 'PASS_TRUE_DUAL_LIVE_STRUCTURED_ADJUDICATION');
  assert.equal(receipt.packetSha256, bind.packetSha256);
  assert.equal(receipt.gptExecutionMode, 'LIVE_OPENAI_API');
  assert.equal(receipt.geminiExecutionMode, 'LIVE_GEMINI_API');
  assert.equal(receipt.adjudicationComputed, true);
  assert.equal(receipt.overallClassification, 'CONVERGED');
} finally {
  fs.rmSync(openaiFile, { force: true });
  fs.rmSync(geminiFile, { force: true });
}

console.log('PASS true dual-live API provider adjudicator');
