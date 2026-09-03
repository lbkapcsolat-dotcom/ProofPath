import assert from 'node:assert/strict';
import { buildStructuredClaimPrompt, normalizeStructuredClaimRun, compareStructuredClaimVectors } from './structured-claim-contract.mjs';

const bind={gate:'CORPUS_COLOSSUM_GEMINI_READ_ONLY_BIND_V1',mode:'READ_ONLY',writeAuthority:false,packetSha256:'a'.repeat(64),authority:{systemMaster:'A3460',systemBoot:'BOOT2106',corpusMaster:'A3449',corpusBoot:'BOOT2095'},sources:[{id:'s1'}],question:'q'};
const prompt=buildStructuredClaimPrompt('GPT',bind);
assert.match(prompt,/CLAIM_SCHEMA=ALPHA_NSH_STRUCTURED_CLAIM_VECTOR_V1/);
assert.match(prompt,/claim_id/);

const base={consumer:'GPT',packetSha256:bind.packetSha256,claims:[{claim_id:'WRITE_BOUNDARY',proposition:'Write boundary is read only.',polarity:'AFFIRM',scope:'system',authority_basis:'A3460/BOOT2106',provenance_ids:['s1'],uncertainty:'',hold_trigger:'',write_intent:false,metric_key:'',metric_value:'',metric_unit:''}]};
const gpt=normalizeStructuredClaimRun(base,bind);
const gem=normalizeStructuredClaimRun({...base,consumer:'GEMINI'},bind);
let r=compareStructuredClaimVectors({bind,gpt,gemini:gem});
assert.equal(r.overallClassification,'CONVERGED');
assert.deepEqual(r.claims[0].relations,['AGREEMENT']);

const contradiction=normalizeStructuredClaimRun({...base,consumer:'GEMINI',claims:[{...base.claims[0],polarity:'DENY'}]},bind);
r=compareStructuredClaimVectors({bind,gpt,gemini:contradiction});
assert.ok(r.claims[0].relations.includes('DIRECT_CONTRADICTION'));
assert.equal(r.overallClassification,'MATERIAL_DIVERGENCE');

const omitted=normalizeStructuredClaimRun({...base,consumer:'GEMINI',claims:[]},bind);
r=compareStructuredClaimVectors({bind,gpt,gemini:omitted});
assert.ok(r.claims[0].relations.includes('OMISSION_GEMINI'));

const scopeShift=normalizeStructuredClaimRun({...base,consumer:'GEMINI',claims:[{...base.claims[0],scope:'local'}]},bind);
r=compareStructuredClaimVectors({bind,gpt,gemini:scopeShift});
assert.ok(r.claims[0].relations.includes('SCOPE_SHIFT'));

const authorityConflict=normalizeStructuredClaimRun({...base,consumer:'GEMINI',claims:[{...base.claims[0],authority_basis:'OTHER'}]},bind);
r=compareStructuredClaimVectors({bind,gpt,gemini:authorityConflict});
assert.ok(r.claims[0].relations.includes('AUTHORITY_CONFLICT'));

const metricConflict=normalizeStructuredClaimRun({...base,consumer:'GEMINI',claims:[{...base.claims[0],metric_key:'count',metric_value:'2',metric_unit:'items'}]},bind);
const gptMetric=normalizeStructuredClaimRun({...base,claims:[{...base.claims[0],metric_key:'count',metric_value:'1',metric_unit:'items'}]},bind);
r=compareStructuredClaimVectors({bind,gpt:gptMetric,gemini:metricConflict});
assert.ok(r.claims[0].relations.includes('METRIC_CONFLICT'));

const uncertainty=normalizeStructuredClaimRun({...base,consumer:'GEMINI',claims:[{...base.claims[0],uncertainty:'provider state may change'}]},bind);
r=compareStructuredClaimVectors({bind,gpt,gemini:uncertainty});
assert.ok(r.claims[0].relations.includes('UNCERTAINTY_ASYMMETRY'));

assert.throws(()=>normalizeStructuredClaimRun({...base,claims:[{...base.claims[0],write_intent:true}]},bind),/write intent/i);
assert.throws(()=>normalizeStructuredClaimRun({...base,claims:[{...base.claims[0],provenance_ids:['evil']}]},bind),/unknown provenance/i);
console.log('PASS structured claim vector contract');
