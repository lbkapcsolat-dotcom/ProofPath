import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

const run = spawnSync(process.execPath, ['gemini-live-dual-structured-claim-run.mjs'], {
  encoding: 'utf8',
  env: { ...process.env, GEMINI_API_KEY: 'test-key-must-never-reach-network' }
});

assert.equal(run.status, 2, 'unproven credential rotation must HOLD with exit 2');
assert.equal(run.stderr, '');
const receipt = JSON.parse(run.stdout.trim());
assert.equal(receipt.status, 'HOLD_GEMINI_CREDENTIAL_ROTATION_NOT_PROVEN');
assert.equal(receipt.liveInferenceExecuted, false);
assert.equal(receipt.credentialRotationProven, false);
assert.equal(receipt.oldCredentialRevoked, false);
assert.equal(receipt.zeroCorpusWrites, true);
assert.equal(receipt.authorityMutation, false);
assert.equal(receipt.pointerPromotion, false);
assert.equal(receipt.globalBind, false);
assert.equal(receipt.runtimeAdmission, false);
assert.equal(receipt.externalActuation, false);

console.log('PASS Gemini true dual-live credential rotation guard');
