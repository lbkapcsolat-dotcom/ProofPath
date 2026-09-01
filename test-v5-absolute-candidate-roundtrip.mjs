import assert from 'node:assert/strict';
import fs from 'node:fs';

const enginePath = new URL('./v5-absolute-candidate.mjs', import.meta.url);
assert.equal(
  fs.existsSync(enginePath),
  true,
  'V5 Absolute Candidate engine must exist before deterministic round-trip can pass'
);

console.log('PASS V5 absolute candidate engine presence');
