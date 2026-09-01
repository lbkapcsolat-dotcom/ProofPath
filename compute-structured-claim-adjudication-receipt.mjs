import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { normalizeStructuredClaimRun, compareStructuredClaimVectors, STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url), 'utf8'));
const bind = await buildCorpusCallosumReadOnlyBind(fixture);
const gptRaw = JSON.parse(fs.readFileSync(new URL('./gpt-current-authority-structured-run.json', import.meta.url), 'utf8'));
const geminiReceipt = JSON.parse(fs.readFileSync(process.argv[2] || 'gemini-live-structured-claim-receipt.json', 'utf8'));

const hold = {
  gate: 'ALPHA_NSH_STRUCTURED_CLAIM_VECTOR_AND_ADJUDICATION_V1',
  status: 'HOLD_DUAL_MODEL_STRUCTURED_CLAIM_EXECUTION_INCOMPLETE',
  claimSchema: STRUCTURED_CLAIM_SCHEMA,
  packetSha256: bind.packetSha256,
  gptStructuredVectorPresent: true,
  gptExecutionMode: 'STATIC_AUDITABLE_FIXTURE_NOT_LIVE_PROVIDER_CALL',
  geminiReceiptStatus: geminiReceipt.status || null,
  adjudicationComputed: false,
  truthSelection: 'NONE__HUMAN_ADJUDICATION_PRESERVED',
  zeroCorpusWrites: true,
  authorityMutation: false,
  pointerPromotion: false,
  runtimeAdmission: false,
  externalActuation: false
};

if (geminiReceipt.status !== 'PASS_GEMINI_LIVE_STRUCTURED_CLAIM_VECTOR' || !geminiReceipt.run) {
  console.log(JSON.stringify(hold));
  process.exit(0);
}

const gpt = normalizeStructuredClaimRun(gptRaw, bind);
const gemini = normalizeStructuredClaimRun(geminiReceipt.run, bind);
const adjudication = compareStructuredClaimVectors({ bind, gpt, gemini });
console.log(JSON.stringify({
  gate: 'ALPHA_NSH_STRUCTURED_CLAIM_VECTOR_AND_ADJUDICATION_V1',
  status: 'PASS_STRUCTURED_CLAIM_ADJUDICATION__HOLD_GPT_LIVE_PROVIDER_EXECUTION_NOT_PROVEN',
  adjudicationComputed: true,
  gptExecutionMode: 'STATIC_AUDITABLE_FIXTURE_NOT_LIVE_PROVIDER_CALL',
  geminiExecutionMode: 'LIVE_PROVIDER_CALL',
  ...adjudication
}));
