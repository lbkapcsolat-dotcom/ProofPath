import test from 'node:test';
import assert from 'node:assert/strict';
import { createSession, recordDiagnosis, recordRetry } from '../core/session.js';
import { rerankWithOptionalModel } from '../core/modelAdapter.js';

test('session stores only current local workflow fields', () => {
  assert.deepEqual(Object.keys(createSession()), ['problem','attempt','diagnosis','hint','retry','retryOutcome']);
});

test('state transitions are immutable', () => {
  const a=createSession();
  const b=recordDiagnosis(a,{problem:'p',attempt:'a',diagnosis:{id:'unknown'},hint:{text:'h'}});
  assert.notEqual(a,b);
  assert.equal(a.problem,'');
  assert.equal(b.problem,'p');
  const c=recordRetry(b,'retry','uncertain');
  assert.equal(c.retry,'retry');
  assert.equal(c.retryOutcome,'uncertain');
});

test('optional model adapter deterministically returns input candidates in V1', async () => {
  const candidates=[{id:'unknown',score:0.4,evidence:[]}];
  assert.deepEqual(await rerankWithOptionalModel(candidates,{}), {candidates,source:'deterministic'});
});
