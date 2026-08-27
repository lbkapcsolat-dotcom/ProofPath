import test from 'node:test';
import assert from 'node:assert/strict';
import { MISCONCEPTIONS, getMisconception } from '../core/taxonomy.js';

const ids = ['sign_handling','operation_order','equality_as_action','variable_isolation','proportional_reasoning','equilibrium_vs_stability','velocity_vs_acceleration','insufficient_evidence','unknown'];

test('taxonomy exposes the exact bounded V1 classes', () => {
  assert.deepEqual(MISCONCEPTIONS.map(x => x.id), ids);
});

test('every class has a confidence ceiling and one safe hint template', () => {
  for (const item of MISCONCEPTIONS) {
    assert.equal(typeof item.confidenceCeiling, 'number');
    assert.ok(item.confidenceCeiling >= 0 && item.confidenceCeiling <= 0.9);
    assert.equal(typeof item.hintTemplate, 'string');
    assert.ok(item.hintTemplate.length > 10);
  }
});

test('unknown is the fail-closed fallback', () => {
  assert.equal(getMisconception('missing'), null);
  assert.equal(getMisconception('unknown').confidenceCeiling, 0.4);
});
