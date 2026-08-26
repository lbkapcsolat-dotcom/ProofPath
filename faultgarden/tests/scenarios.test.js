import test from 'node:test';
import assert from 'node:assert/strict';
import { SCENARIOS, runScenario } from '../src/scenarios.js';
const ids=['NORMAL_EXECUTION','DUPLICATE_DISPATCH','CRASH_AFTER_DISPATCH','CRASH_BEFORE_RESPONSE_PERSIST','STALE_HOST_RESPONSE','TWO_HOST_RACE','TAMPERED_LEDGER_EVENT','DETERMINISTIC_REPLAY'];
test('catalog contains exactly eight required scenarios',()=>assert.deepEqual(Object.keys(SCENARIOS),ids));
for(const id of ids)test(`${id} runs deterministically`,()=>{const a=runScenario(id),b=runScenario(id);assert.deepEqual(a.events,b.events);assert.equal(a.scenario.id,id)});