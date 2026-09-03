import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { compareDualLiveClaimVectors, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';
import { verifyOpenAiLiveStructuredReceipt, OPENAI_LIVE_PASS } from './openai-live-contract.mjs';
import { verifyGeminiLiveStructuredReceipt, GEMINI_LIVE_PASS } from './gemini-live-contract.mjs';
import { emitReceiptAndExit } from './gate-status.mjs';

const GATE = 'ALPHA_CORPUS_CALLOSUM_SECURITY_AND_TRUE_DUAL_LIVE_CLOSE_V1';
const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);
const openaiReceipt = JSON.parse(fs.readFileSync(process.argv[2] || 'openai-live-dual-structured-claim-receipt.json', 'utf8'));
const geminiReceipt = JSON.parse(fs.readFileSync(process.argv[3] || 'gemini-live-dual-structured-claim-receipt.json', 'utf8'));

const base = {
  gate: GATE,
  status: 'HOLD_DUAL_LIVE_STRUCTURED_EXECUTION_INCOMPLETE',
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
  claimOntology: DUAL_LIVE_CLAIM_ONTOLOGY_ID,
  packetSha256: bind.packetSha256,
  openaiReceiptStatus: openaiReceipt.status || null,
  geminiReceiptStatus: geminiReceipt.status || null,
  gptExecutionMode: openaiReceipt.executionMode || null,
  geminiExecutionMode: geminiReceipt.executionMode || null,
  adjudicationComputed: false,
  truthSelection: 'NONE__HUMAN_ADJUDICATION_PRESERVED',
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  runtimeAdmission: false,
  externalActuation: false
};

if (openaiReceipt.status !== OPENAI_LIVE_PASS || !openaiReceipt.run) {
  emitReceiptAndExit({ ...base, status: 'HOLD_OPENAI_TRUE_LIVE_STRUCTURED_VECTOR_MISSING' });
}
if (geminiReceipt.status !== GEMINI_LIVE_PASS || !geminiReceipt.run) {
  emitReceiptAndExit({ ...base, status: 'HOLD_GEMINI_TRUE_LIVE_STRUCTURED_VECTOR_MISSING' });
}

let gpt;
try {
  gpt = verifyOpenAiLiveStructuredReceipt(openaiReceipt, bind);
} catch (error) {
  emitReceiptAndExit({
    ...base,
    status: `HOLD_OPENAI_TRUE_LIVE_RECEIPT_REJECTED__${String(error?.message || 'unknown').replace(/\s+/g, '_')}`
  });
}

let gemini;
try {
  gemini = verifyGeminiLiveStructuredReceipt(geminiReceipt, bind);
} catch (error) {
  emitReceiptAndExit({
    ...base,
    status: `HOLD_GEMINI_TRUE_LIVE_RECEIPT_REJECTED__${String(error?.message || 'unknown').replace(/\s+/g, '_')}`
  });
}

const adjudication = compareDualLiveClaimVectors({ bind, gpt, gemini });
emitReceiptAndExit({
  ...base,
  status: 'PASS_TRUE_DUAL_LIVE_STRUCTURED_ADJUDICATION',
  adjudicationComputed: true,
  gptExecutionMode: openaiReceipt.executionMode,
  geminiExecutionMode: geminiReceipt.executionMode,
  ...adjudication
});
