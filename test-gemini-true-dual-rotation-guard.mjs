import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

const scripts = [
  'gemini-live-zero-spend-preflight.mjs',
  'gemini-live-same-packet-run.mjs',
  'gemini-live-structured-claim-run.mjs',
  'gemini-live-dual-structured-claim-run.mjs'
];

for (const script of scripts) {
  const run = spawnSync(process.execPath, [script], {
    encoding: 'utf8',
    env: { ...process.env, GEMINI_API_KEY: 'test-key-must-never-reach-network' }
  });

  assert.equal(run.status, 2, `${script}: unproven rotation must HOLD with exit 2`);
  assert.equal(run.stderr, '', `${script}: no secret-bearing stderr expected`);
  const receipt = JSON.parse(run.stdout.trim());
  assert.equal(receipt.status, 'HOLD_GEMINI_CREDENTIAL_ROTATION_NOT_PROVEN', `${script}: rotation HOLD required`);
  assert.equal(receipt.liveInferenceExecuted, false, `${script}: no live inference before rotation`);
  assert.equal(receipt.credentialRotationProven, false, `${script}: rotation remains unproven`);
  assert.equal(receipt.oldCredentialRevoked, false, `${script}: old credential remains unrevoked`);
  assert.equal(receipt.zeroCorpusWrites, true);
  assert.equal(receipt.authorityMutation, false);
  assert.equal(receipt.pointerPromotion, false);
  assert.equal(receipt.globalBind, false);
  if ('runtimeAdmission' in receipt) assert.equal(receipt.runtimeAdmission, false);
  assert.equal(receipt.externalActuation, false);
}

console.log('PASS Gemini credential rotation guard on all network surfaces');
