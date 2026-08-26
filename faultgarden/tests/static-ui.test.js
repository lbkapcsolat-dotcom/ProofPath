import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const html=fs.readFileSync(new URL('../index.html',import.meta.url),'utf8');
const required=['scenario-select','run-btn','step-btn','reset-btn','replay-btn','tamper-btn','host-a','host-b','timeline','ledger-body','invariants-body','verdict-card','download-btn'];
for(const id of required)test(`UI contains #${id}`,()=>assert.match(html,new RegExp(`id=["']${id}["']`)));
test('UI has accessible main label',()=>assert.match(html,/aria-label="FaultGarden reliability simulator"/));
test('UI exposes claim ceiling',()=>assert.match(html,/INTERACTIVE_DETERMINISTIC_RELIABILITY_SIMULATOR/));