import assert from 'node:assert/strict';
import {
  DUAL_LIVE_CLAIM_ONTOLOGY,
  normalizeDualLiveClaimRun,
  compareDualLiveClaimVectors,
  verifyLiveGptSessionReceipt
} from './dual-live-structured-claim-contract.mjs';

const bind={gate:'CORPUS_COLOSSUM_GEMINI_READ_ONLY_BIND_V1',mode:'READ_ONLY',writeAuthority:false,packetSha256:'a'.repeat(64),sources:[{id:'s1'}],question:'q'};
const claim=(claim_id, overrides={})=>({claim_id,proposition:`${claim_id} proposition`,polarity:'AFFIRM',scope:'system',authority_basis:'A3460/BOOT2106',provenance_ids:['s1'],uncertainty:'',hold_trigger:'',write_intent:false,metric_key:'',metric_value:'',metric_unit:'',...overrides});
const exact=DUAL_LIVE_CLAIM_ONTOLOGY.map(x=>claim(x.claim_id));
const gpt=normalizeDualLiveClaimRun({consumer:'GPT',packetSha256:bind.packetSha256,claims:exact},bind);
const gem=normalizeDualLiveClaimRun({consumer:'GEMINI',packetSha256:bind.packetSha256,claims:exact},bind);
const out=compareDualLiveClaimVectors({bind,gpt,gemini:gem});
assert.equal(out.overallClassification,'CONVERGED');
assert.equal(out.claimOntology,'ALPHA_NSH_DUAL_LIVE_CLAIM_ONTOLOGY_V1');
assert.throws(()=>normalizeDualLiveClaimRun({consumer:'GPT',packetSha256:bind.packetSha256,claims:exact.slice(1)},bind),/canonical claim set/i);
const changed=exact.map(c=>c.claim_id==='WRITE_BOUNDARY'?{...c,polarity:'DENY'}:c);
const gem2=normalizeDualLiveClaimRun({consumer:'GEMINI',packetSha256:bind.packetSha256,claims:changed},bind);
const out2=compareDualLiveClaimVectors({bind,gpt,gemini:gem2});
assert.equal(out2.overallClassification,'MATERIAL_DIVERGENCE');
assert.ok(out2.claims.find(c=>c.claim_id==='WRITE_BOUNDARY').relations.includes('DIRECT_CONTRADICTION'));
const fakeReceipt={status:'PASS_GPT_LIVE_CHATGPT_SESSION_STRUCTURED_CLAIM_VECTOR',packetSha256:bind.packetSha256,claimSchema:'ALPHA_NSH_STRUCTURED_CLAIM_VECTOR_V1',claimOntology:'ALPHA_NSH_DUAL_LIVE_CLAIM_ONTOLOGY_V1',provider:'OpenAI',providerSurface:'ChatGPT',executionMode:'LIVE_CHATGPT_SESSION_NOT_API_PROVIDER_RECEIPT',liveInferenceExecuted:true,zeroSpendPolicyPreserved:true,zeroCorpusWrites:true,authorityMutation:false,pointerPromotion:false,globalBind:false,runtimeAdmission:false,externalActuation:false,run:{consumer:'GPT',packetSha256:bind.packetSha256,claims:exact},receipt_sha256:'bad'};
assert.throws(()=>verifyLiveGptSessionReceipt(fakeReceipt,bind),/self-seal/i);
console.log('PASS dual-live structured claim ontology');
