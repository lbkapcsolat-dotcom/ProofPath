import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeEvidence } from '../src/evidence.mjs';

test('blank claim or evidence is insufficient', () => {
  assert.equal(analyzeEvidence('', 'some evidence').verdict, 'INSUFFICIENT');
  assert.equal(analyzeEvidence('some claim', '').verdict, 'INSUFFICIENT');
});

test('explicit negation conflict is contradicted', () => {
  const result = analyzeEvidence('The river is clean', 'The river is not clean according to the sample');
  assert.equal(result.verdict, 'CONTRADICTED');
});

test('strong shared terms without conflict is supported', () => {
  const result = analyzeEvidence('Solar panels reduced school electricity use', 'School electricity use was reduced after solar panels were installed');
  assert.equal(result.verdict, 'SUPPORTED');
});
