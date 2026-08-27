import test from 'node:test';
import assert from 'node:assert/strict';
import { extractFeatures } from '../core/features.js';
import { evaluateRetry } from '../core/retry.js';

test('corrected canonical retry improves', () => {
  const r = extractFeatures('Solve 3x + 5 = 20.', '3x = 15, x = 5', 'algebra');
  assert.equal(evaluateRetry({ id:'sign_handling' }, r), 'improved');
});

test('repeating 3x=25 keeps the same pattern', () => {
  const r = extractFeatures('Solve 3x + 5 = 20.', '3x = 25', 'algebra');
  assert.equal(evaluateRetry({ id:'sign_handling' }, r), 'same_pattern');
});

test('unrelated retry is uncertain', () => {
  const r = extractFeatures('Solve 3x + 5 = 20.', 'I guessed.', 'algebra');
  assert.equal(evaluateRetry({ id:'sign_handling' }, r), 'uncertain');
});
