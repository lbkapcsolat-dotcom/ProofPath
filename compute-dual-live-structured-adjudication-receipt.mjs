import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { verifyLiveGptSessionReceipt, normalizeDualLiveClaimRun, compareDualLiveClaimVectors, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';

const GATE='ALPHA_NSH_DUAL_LIVE_STRUCTURED_CLAIM_EXECUTION_AND_ADJUDICATION_V1';
const fixture=JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json',import.meta.url),'utf8'));
const bind=await buildCorpusCallosumReadOnlyBind(fixture);
const gptReceipt=JSON.parse(fs.readFileSync(process.argv[2]||'gpt-live-chatgpt-session-structured-receipt.json','utf8'));
const geminiReceipt=JSON.parse(fs.readFileSync(process.argv[3]||'gemini-live-dual-structured-claim-receipt.json','utf8'));
const hold={gate:GATE,status:'HOLD_DUAL_LIVE_STRUCTURED_EXECUTION_INCOMPLETE',claimSchema:STRUCTURED_CLAIM_SCHEMA,claimOntology:DUAL_LIVE_CLAIM_ONTOLOGY_ID,packetSha256:bind.packetSha256,gptReceiptStatus:gptReceipt.status||null,gptExecutionMode:gptReceipt.executionMode||null,geminiReceiptStatus:geminiReceipt.status||null,adjudicationComputed:false,truthSelection:'NONE__HUMAN_ADJUDICATION_PRESERVED',zeroCorpusWrites:true,authorityMutation:false,pointerPromotion:false,runtimeAdmission:false,externalActuation:false};
if(gptReceipt.status!=='PASS_GPT_LIVE_CHATGPT_SESSION_STRUCTURED_CLAIM_VECTOR'||!gptReceipt.run){console.log(JSON.stringify({...hold,status:'HOLD_GPT_LIVE_STRUCTURED_VECTOR_MISSING'}));process.exit(0);}
if(gptReceipt.packetSha256!==bind.packetSha256||gptReceipt.claimOntology!==DUAL_LIVE_CLAIM_ONTOLOGY_ID){console.log(JSON.stringify({...hold,status:'HOLD_GPT_LIVE_RECEIPT_IDENTITY_MISMATCH'}));process.exit(0);}
if(geminiReceipt.status!=='PASS_GEMINI_DUAL_LIVE_STRUCTURED_CLAIM_VECTOR'||!geminiReceipt.run){console.log(JSON.stringify({...hold,status:'HOLD_GEMINI_DUAL_LIVE_STRUCTURED_VECTOR_MISSING'}));process.exit(0);}
let gpt; try { gpt=verifyLiveGptSessionReceipt(gptReceipt,bind); } catch(error) { console.log(JSON.stringify({...hold,status:`HOLD_GPT_LIVE_RECEIPT_REJECTED__${String(error?.message||'unknown').replace(/\s+/g,'_')}`})); process.exit(0); }
const gemini=normalizeDualLiveClaimRun(geminiReceipt.run,bind);
const adjudication=compareDualLiveClaimVectors({bind,gpt,gemini});
console.log(JSON.stringify({gate:GATE,status:'PASS_DUAL_LIVE_MODEL_SURFACE_STRUCTURED_ADJUDICATION__HOLD_DUAL_API_PROVIDER_EXECUTION_NOT_PROVEN',adjudicationComputed:true,gptExecutionMode:gptReceipt.executionMode,geminiExecutionMode:'LIVE_GEMINI_API_PROVIDER_CALL',providerSignedGptReceipt:gptReceipt.providerSignedReceipt===true,...adjudication}));
