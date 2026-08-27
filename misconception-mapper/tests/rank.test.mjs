import test from 'node:test';
import assert from 'node:assert/strict';
import { extractFeatures } from '../core/features.js';
import { rankMisconceptions } from '../core/rank.js';

test('canonical algebra case ranks sign handling first and respects ceiling', () => {
  const ranked = rankMisconceptions(extractFeatures('Solve 3x + 5 = 20.', '3x = 25, x = 8.33', 'algebra'));
  assert.equal(ranked[0].id, 'sign_handling');
  assert.ok(ranked[0].confidence <= 0.88);
});

test('automatic stability wording ranks equilibrium confusion first', () => {
  const ranked = rankMisconceptions(extractFeatures('Is every equilibrium stable?', 'Yes, equilibrium means it is stable.', 'physics'));
  assert.equal(ranked[0].id, 'equilibrium_vs_stability');
});

test('no evidence falls back to unknown', () => {
  const ranked = rankMisconceptions(extractFeatures('Explain this.', 'I am not sure.', ''));
  assert.equal(ranked[0].id, 'unknown');
  assert.ok(ranked[0].confidence <= 0.4);
});
