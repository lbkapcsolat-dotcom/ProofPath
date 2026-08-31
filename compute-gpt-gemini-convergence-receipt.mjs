import fs from 'node:fs';
import {
  buildCorpusCallosumReadOnlyBind,
  normalizeReasoningRun,
  buildConvergenceReceipt
} from './corpus-callosum-contract.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);
const gptRaw = JSON.parse(fs.readFileSync(new URL('./gpt-current-authority-run.json', import.meta.url), 'utf8'));
const geminiReceipt = JSON.parse(fs.readFileSync(process.argv[2] || 'gemini-live-same-packet-receipt.json', 'utf8'));

const hold = {
  gate: 'GPT_GEMINI_CONVERGENCE_DIVERGENCE_RECEIPT_V1',
  status: 'HOLD_DEPENDENCY_GEMINI_LIVE_SAME_PACKET_EXECUTION_MISSING',
  packetSha256: bind.packetSha256,
  systemAuthority: `${bind.authority.systemMaster}/${bind.authority.systemBoot}`,
  corpusRouter: `${bind.authority.corpusMaster}/${bind.authority.corpusBoot}`,
  gptRunPresent: true,
  geminiReceiptStatus: geminiReceipt.status || null,
  convergenceComputed: false,
  classification: null,
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  globalBind: false,
  externalActuation: false
};

if (geminiReceipt.status !== 'PASS_GEMINI_LIVE_SAME_PACKET_EXECUTION' || !geminiReceipt.run) {
  console.log(JSON.stringify(hold));
  process.exit(0);
}

const gpt = normalizeReasoningRun(gptRaw, bind);
const gemini = normalizeReasoningRun(geminiReceipt.run, bind);
const comparison = buildConvergenceReceipt({ bind, gpt, gemini });
console.log(JSON.stringify({
  gate: 'GPT_GEMINI_CONVERGENCE_DIVERGENCE_RECEIPT_V1',
  status: 'PASS_COMPARISON_COMPUTED',
  convergenceComputed: true,
  ...comparison
}));
