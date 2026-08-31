import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';

const auth = JSON.parse(fs.readFileSync(new URL('./gemini-live-execution-authorization.json', import.meta.url), 'utf8'));
assert.equal(auth.authorized, true, 'proven Free Tier credential bind must be explicitly authorized');
assert.equal(auth.keyProjectNumber, '1066743013619');
assert.equal(auth.keyProjectId, 'gen-lang-client-0055837645');
assert.equal(auth.billingTier, 'FREE_TIER');
assert.equal(auth.billingActivated, false);
assert.equal(auth.forbidBillingActivation, true);
assert.equal(auth.forbidKeyInSource, true);
assert.equal(auth.forbidKeyInChat, true);
assert.equal(auth.packetSha256, 'c934b241c00f3a9cf15f56f9239f96471a0d721d8161865cbcaa6c8165493024');

// Negative drill: even with a proven Free Tier project bind, absence of the
// runtime secret must fail closed before any model-surface or inference call.
const output = execFileSync(process.execPath, ['gemini-live-same-packet-run.mjs'], {
  encoding: 'utf8',
  env: { ...process.env, GEMINI_API_KEY: '' }
}).trim();
const receipt = JSON.parse(output);
assert.equal(receipt.status, 'HOLD_GEMINI_API_KEY_NOT_CONFIGURED_IN_GITHUB_ACTIONS');
assert.equal(receipt.liveInferenceExecuted, false);
assert.equal(receipt.freeTierAuthorized, true);
assert.equal(receipt.authenticatedModelSurface, false);
assert.equal(receipt.zeroCorpusWrites, true);
assert.equal(receipt.authorityMutation, false);
assert.equal(receipt.pointerPromotion, false);
assert.equal(receipt.globalBind, false);
assert.equal(receipt.externalActuation, false);

fs.writeFileSync('gemini-live-same-packet-receipt.test.json', JSON.stringify(receipt));
const comparisonOutput = execFileSync(process.execPath, [
  'compute-gpt-gemini-convergence-receipt.mjs',
  'gemini-live-same-packet-receipt.test.json'
], { encoding: 'utf8' }).trim();
const comparison = JSON.parse(comparisonOutput);
assert.equal(comparison.status, 'HOLD_DEPENDENCY_GEMINI_LIVE_SAME_PACKET_EXECUTION_MISSING');
assert.equal(comparison.convergenceComputed, false);
assert.equal(comparison.classification, null);
fs.unlinkSync('gemini-live-same-packet-receipt.test.json');

console.log('PASS Gemini live pipeline fail-closed');
