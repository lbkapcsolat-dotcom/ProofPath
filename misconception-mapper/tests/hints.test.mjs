import test from 'node:test';
import assert from 'node:assert/strict';
import { buildHint } from '../core/hints.js';

test('known diagnosis gets exactly one approved non-answer hint', () => {
  const h = buildHint({ id:'sign_handling' });
  assert.equal(typeof h.text, 'string');
  assert.equal(h.revealsFinalAnswer, false);
  assert.equal(h.text.includes('x = 5'), false);
});

test('unknown gets clarification hint', () => {
  assert.match(buildHint({ id:'unknown' }).text, /intermediate step|rule/i);
});
