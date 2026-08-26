import test from 'node:test';
import assert from 'node:assert/strict';
import { buildRunLedger, replayLedger } from '../src/replay.js';
import { verifyInvariants } from '../src/invariants.js';
for(const id of ['NORMAL_EXECUTION','TWO_HOST_RACE','STALE_HOST_RESPONSE','CRASH_BEFORE_RESPONSE_PERSIST','DETERMINISTIC_REPLAY'])test(`${id} replay/invariants are bounded`,async()=>{const run=await buildRunLedger(id);const replay=await replayLedger(run.ledger);const inv=await verifyInvariants(run,replay);assert.equal(inv.every(x=>['PASS','HOLD','EXPECTED_REJECTION'].includes(x.status)),true)});
test('untampered deterministic replay matches final digest',async()=>{const run=await buildRunLedger('DETERMINISTIC_REPLAY');const replay=await replayLedger(run.ledger);assert.equal(replay.stateDigest,run.stateDigest)});
test('two host race has one canonical winner',async()=>{const run=await buildRunLedger('TWO_HOST_RACE');assert.equal(run.state.commitCount,1);assert.equal(run.state.canonicalCommit.hostId,'B')});
test('tampered ledger fails closed',async()=>{const run=await buildRunLedger('TAMPERED_LEDGER_EVENT');assert.equal(run.ledgerValid,false)});