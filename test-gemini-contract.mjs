import assert from 'node:assert/strict';
import { lockAuthoritativeVerdict, buildGeminiPrompt } from './gemini-contract.js';

const authoritative = {
  status: 'READY',
  label: 'INSUFFICIENT',
  probabilities: { SUPPORTED: 0.2, CONTRADICTED: 0.1, INSUFFICIENT: 0.7 }
};

const hostileGemini = {
  verdict: 'SUPPORTED',
  explanation: 'The evidence is interesting but incomplete.',
  nextEvidenceStep: 'Find an independent source that directly measures the claim.'
};

const locked = lockAuthoritativeVerdict(authoritative, hostileGemini);
assert.equal(locked.label, 'INSUFFICIENT', 'Gemini must never override the classifier verdict');
assert.deepEqual(locked.probabilities, authoritative.probabilities, 'Gemini must never alter classifier probabilities');
assert.equal(locked.explanation, hostileGemini.explanation);
assert.equal(locked.nextEvidenceStep, hostileGemini.nextEvidenceStep);
assert.equal('verdict' in locked, false, 'Gemini-proposed verdict fields must be discarded');

const prompt = buildGeminiPrompt({
  claim: 'A school intervention improves attendance.',
  evidence: 'One class reported higher attendance after the intervention.',
  authoritative
});
assert.match(prompt, /INSUFFICIENT/);
assert.match(prompt, /must not change/i);
assert.match(prompt, /educational/i);

console.log('PASS Gemini contract: classifier authority preserved');
