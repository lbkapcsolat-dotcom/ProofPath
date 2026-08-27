import test from 'node:test';
import assert from 'node:assert/strict';
import { extractFeatures } from '../core/features.js';
import { rankMisconceptions } from '../core/rank.js';

test('canonical sign error ranks first within ceiling', () => {
  const r = rankMisconceptions(extractFeatures('Solve 3x + 5 = 20.', '3x = 25, x = 8.33', 'algebra'));
  assert.equal(r[0].id, 'sign_handling');
  assert.ok(r[0].score <= 0.88);
});

test('automatic-stability claim ranks equilibrium confusion first', () => {
  const r = rankMisconceptions(extractFeatures('Is every equilibrium stable?', 'Yes, equilibrium means stable.', 'physics'));
  assert.equal(r[0].id, 'equilibrium_vs_stability');
});

test('unmatched text returns unknown rather than fabricated diagnosis', () => {
  const r = rankMisconceptions(extractFeatures('Explain this.', 'I am not sure.', 'algebra'));
  assert.equal(r[0].id, 'unknown');
});
