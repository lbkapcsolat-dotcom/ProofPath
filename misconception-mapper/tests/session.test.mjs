import test from 'node:test';
import assert from 'node:assert/strict';
import { createSession, applyDiagnosis, applyRetry } from '../core/session.js';
import { rerankWithOptionalModel } from '../core/modelAdapter.js';

test('session state is local plain data with no remote dependency', () => {
  const s = createSession({ problem:'p', attempt:'a', concept:'algebra' });
  assert.deepEqual(Object.keys(s).sort(), ['attempt','concept','diagnosis','hint','problem','retry','retryOutcome'].sort());
  assert.equal(s.retry, '');
});

test('diagnosis and retry transitions are immutable', () => {
  const s1 = createSession({ problem:'p', attempt:'a', concept:'algebra' });
  const s2 = applyDiagnosis(s1, { id:'unknown' }, 'clarify?');
  const s3 = applyRetry(s2, 'new', { status:'uncertain' });
  assert.equal(s1.diagnosis, null);
  assert.equal(s2.retry, '');
  assert.equal(s3.retry, 'new');
});

test('optional model adapter deterministically falls back when disabled', async () => {
  const ranked = [{ id:'sign_handling', score:1, confidence:0.88 }];
  const out = await rerankWithOptionalModel(ranked, { enabled:false });
  assert.deepEqual(out, ranked);
});
