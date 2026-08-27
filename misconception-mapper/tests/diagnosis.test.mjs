import test from 'node:test';
import assert from 'node:assert/strict';
import { selectDiagnosis } from '../core/diagnosis.js';

test('strong top candidate becomes calibrated likely diagnosis', () => {
  const d = selectDiagnosis([{ id:'sign_handling', score:0.88, evidence:['sign evidence'] }]);
  assert.equal(d.status, 'likely');
  assert.equal(d.id, 'sign_handling');
  assert.match(d.confidenceText, /likely/i);
});

test('close candidates fail closed to uncertain', () => {
  const d = selectDiagnosis([{ id:'sign_handling', score:0.70, evidence:[] }, { id:'variable_isolation', score:0.65, evidence:[] }]);
  assert.equal(d.status, 'uncertain');
  assert.equal(d.id, 'unknown');
});

test('unknown stays uncertain', () => {
  assert.equal(selectDiagnosis([{ id:'unknown', score:0.4, evidence:[] }]).status, 'uncertain');
});
