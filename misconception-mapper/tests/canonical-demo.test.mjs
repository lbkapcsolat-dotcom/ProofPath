import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeAttempt, analyzeRetry } from '../core/analyze.js';

test('canonical algebra flow diagnoses, hints, retries, and improves', async () => {
  const first = await analyzeAttempt({
    problem:'Solve 3x + 5 = 20.',
    attempt:'3x = 25, x = 8.33',
    concept:'algebra'
  });
  assert.equal(first.diagnosis.id, 'sign_handling');
  assert.equal(first.diagnosis.status, 'likely');
  assert.match(first.hint, /inverse operation/i);
  assert.equal(first.hint.includes('x = 5'), false);

  const second = analyzeRetry(first.session, '3x = 15, x = 5');
  assert.equal(second.retryOutcome.status, 'improved');
});
