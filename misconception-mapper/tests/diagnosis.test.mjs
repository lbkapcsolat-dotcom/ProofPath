import test from 'node:test';
import assert from 'node:assert/strict';
import { selectDiagnosis } from '../core/diagnosis.js';

test('high-confidence candidate becomes bounded diagnosis', () => {
  const d = selectDiagnosis([{ id:'sign_handling', score:1, confidence:0.88 }]);
  assert.equal(d.id, 'sign_handling');
  assert.equal(d.status, 'likely');
  assert.match(d.confidenceLabel, /likely/i);
});

test('close tie fails closed to unknown', () => {
  const d = selectDiagnosis([
    { id:'sign_handling', score:0.8, confidence:0.7 },
    { id:'variable_isolation', score:0.79, confidence:0.69 }
  ]);
  assert.equal(d.id, 'unknown');
  assert.equal(d.status, 'uncertain');
});

test('empty candidates fail closed', () => {
  const d = selectDiagnosis([]);
  assert.equal(d.id, 'unknown');
});
