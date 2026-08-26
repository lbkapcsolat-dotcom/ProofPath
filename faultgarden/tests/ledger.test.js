import test from 'node:test';
import assert from 'node:assert/strict';
import { appendLedgerEvent, verifyLedger, GENESIS_HASH } from '../src/ledger.js';
test('first record binds genesis',async()=>{const l=[];await appendLedgerEvent(l,{type:'X',n:1});assert.equal(l[0].previousHash,GENESIS_HASH);assert.equal((await verifyLedger(l)).valid,true)});
test('same records produce same head',async()=>{const a=[],b=[];for(const x of [{type:'A'},{type:'B'}]){await appendLedgerEvent(a,x);await appendLedgerEvent(b,x)}assert.equal(a.at(-1).recordHash,b.at(-1).recordHash)});
test('changed content changes head',async()=>{const a=[],b=[];await appendLedgerEvent(a,{type:'A',v:1});await appendLedgerEvent(b,{type:'A',v:2});assert.notEqual(a[0].recordHash,b[0].recordHash)});
test('tampering is detected',async()=>{const l=[];await appendLedgerEvent(l,{type:'A'});await appendLedgerEvent(l,{type:'B'});l[0].core.type='EVIL';assert.equal((await verifyLedger(l)).valid,false)});