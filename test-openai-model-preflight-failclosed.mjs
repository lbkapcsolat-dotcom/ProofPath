import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

const run = spawnSync(process.execPath, ['openai-live-model-preflight.mjs'], {
  encoding: 'utf8',
  env: { ...process.env, OPENAI_API_KEY: '' }
});

assert.equal(run.status, 2);
assert.equal(run.stderr, '');
const receipt = JSON.parse(run.stdout.trim());
assert.equal(receipt.status, 'HOLD_OPENAI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS');
assert.equal(receipt.liveInferenceExecuted, false);
assert.equal(receipt.modelTarget, 'gpt-5.6-sol');

console.log('PASS OpenAI model preflight fail-closed behavior');
