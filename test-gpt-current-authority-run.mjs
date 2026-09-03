import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind, normalizeReasoningRun } from './corpus-callosum-contract.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const rawRun = JSON.parse(fs.readFileSync(new URL('./gpt-current-authority-run.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);
const run = normalizeReasoningRun(rawRun, bind);

assert.equal(run.consumer, 'GPT');
assert.equal(run.packetSha256, fixture.expectedPacketSha256);
assert.equal(run.conclusion, 'READ_ONLY_CURRENT_ROUTE_WITH_FAIL_CLOSED_HISTORICAL_RECONCILIATION');
assert.deepEqual(run.provenanceIds, [
  'corpus-discovery-pointer',
  'corpus-router-crossref',
  'current-pointer-top-block',
  'system-authority-crossref'
]);
assert.equal(run.writeIntent, false);
assert.ok(run.reasoning.includes('A3460/BOOT2106'));
assert.ok(run.reasoning.includes('A3449/BOOT2095'));
assert.ok(run.reasoning.includes('HOLD'));

console.log('PASS GPT independent current-authority run');
