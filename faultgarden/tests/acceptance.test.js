import test from 'node:test';
import assert from 'node:assert/strict';
import { executeScenario, exportReceipt } from '../src/run.js';
const expected={NORMAL_EXECUTION:'PASS_SINGLE_COMMIT',DUPLICATE_DISPATCH:'PASS_NO_DOUBLE_COMMIT',CRASH_AFTER_DISPATCH:'PASS_RECOVERY_WITHOUT_DOUBLE_COMMIT',CRASH_BEFORE_RESPONSE_PERSIST:'PASS_NO_UNPROVEN_REDISPATCH',STALE_HOST_RESPONSE:'PASS_STALE_FENCED',TWO_HOST_RACE:'PASS_SINGLE_WINNER',TAMPERED_LEDGER_EVENT:'PASS_TAMPER_DETECTED',DETERMINISTIC_REPLAY:'PASS_REPLAY_HASH_MATCH'};
for(const [id,verdict] of Object.entries(expected)) test(`${id} yields expected verdict`,async()=>assert.equal((await executeScenario(id)).verdict,verdict));
test('same scenario is deterministic',async()=>assert.equal((await executeScenario('NORMAL_EXECUTION')).chainHead,(await executeScenario('NORMAL_EXECUTION')).chainHead));
test('different event content changes chain head',async()=>assert.notEqual((await executeScenario('NORMAL_EXECUTION')).chainHead,(await executeScenario('TWO_HOST_RACE')).chainHead));
test('unknown scenario fails closed',async()=>assert.equal((await executeScenario('NOPE')).verdict,'HOLD_UNKNOWN_SCENARIO'));
test('receipt preserves claim ceiling and hashes',async()=>{const r=JSON.parse(exportReceipt(await executeScenario('DETERMINISTIC_REPLAY')));assert.equal(r.claimCeiling,'INTERACTIVE_DETERMINISTIC_RELIABILITY_SIMULATOR__EDUCATIONAL_TEST_LAB_ONLY');assert.equal(r.stateDigest.length,64);});