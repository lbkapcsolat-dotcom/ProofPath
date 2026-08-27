import test from 'node:test';
import assert from 'node:assert/strict';
import { buildHint } from '../core/hints.js';

test('returns exactly one approved hint for known diagnosis', () => {
  const h = buildHint({ id:'sign_handling' });
  assert.equal(typeof h, 'string');
  assert.ok(h.endsWith('?'));
  assert.equal(h.includes('\n'), false);
});

test('unknown diagnosis gets clarification question', () => {
  const h = buildHint({ id:'unknown' });
  assert.match(h, /intermediate step|rule/i);
});
