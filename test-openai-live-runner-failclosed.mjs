import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

function run(env) {
  return spawnSync(process.execPath, ['openai-live-dual-structured-claim-run.mjs'], {
    encoding: 'utf8',
    env: { ...process.env, ...env }
  });
}

const missingKey = run({ OPENAI_API_KEY: '' });
assert.equal(missingKey.status, 2);
const missingReceipt = JSON.parse(missingKey.stdout.trim());
assert.equal(missingReceipt.status, 'HOLD_OPENAI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS');
assert.equal(missingReceipt.liveInferenceExecuted, false);
assert.equal(missingReceipt.zeroCorpusWrites, true);

const zeroSpendHold = run({ OPENAI_API_KEY: 'test-key-must-never-reach-network' });
assert.equal(zeroSpendHold.status, 2);
const holdReceipt = JSON.parse(zeroSpendHold.stdout.trim());
assert.equal(holdReceipt.status, 'HOLD_OPENAI_ZERO_SPEND_LIVE_INFERENCE_NOT_PROVEN');
assert.equal(holdReceipt.liveInferenceExecuted, false);
assert.equal(holdReceipt.zeroSpendProven, false);
assert.equal(holdReceipt.zeroCorpusWrites, true);
assert.equal(holdReceipt.authorityMutation, false);
assert.equal(holdReceipt.pointerPromotion, false);
assert.equal(holdReceipt.globalBind, false);
assert.equal(holdReceipt.runtimeAdmission, false);
assert.equal(holdReceipt.externalActuation, false);

console.log('PASS OpenAI live runner zero-spend fail-closed behavior');
