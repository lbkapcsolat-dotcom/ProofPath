import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluateRetry } from '../core/retry.js';

test('canonical corrected retry is improved', () => {
  const r = evaluateRetry({ diagnosisId:'sign_handling', problem:'Solve 3x + 5 = 20.', previousAttempt:'3x = 25, x = 8.33', retry:'3x = 15, x = 5', concept:'algebra' });
  assert.equal(r.status, 'improved');
});

test('repeating same canonical sign error is same pattern', () => {
  const r = evaluateRetry({ diagnosisId:'sign_handling', problem:'Solve 3x + 5 = 20.', previousAttempt:'3x = 25', retry:'3x = 25, x = 8.3', concept:'algebra' });
  assert.equal(r.status, 'same pattern');
});

test('unknown diagnosis stays uncertain', () => {
  const r = evaluateRetry({ diagnosisId:'unknown', problem:'Explain.', previousAttempt:'?', retry:'maybe', concept:'' });
  assert.equal(r.status, 'uncertain');
});
