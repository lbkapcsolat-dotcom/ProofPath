
import assert from "node:assert/strict";
import {TRAINING_SET,HOLDOUT_SET,trainSoftmax,predict,extractFeatures} from "./model.js";
const model=trainSoftmax(TRAINING_SET);
let correct=0; const rows=[];
for(const ex of HOLDOUT_SET){
  const p=predict(model,ex.claim,ex.evidence);
  rows.push({expected:ex.label,predicted:p.label,claim:ex.claim,probabilities:p.probabilities});
  if(p.label===ex.label)correct++;
}
assert.equal(correct,10,`Expected 10/10 fixed holdout result, got ${correct}/10`);
assert.equal(extractFeatures("Iron is a metal.","Iron is classified as a metal.").length,12);
assert.equal(predict(model,"Iron is a metal.","Iron is classified as a metal.").claim_ceiling,"EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY");
console.log(JSON.stringify({correct,total:HOLDOUT_SET.length,rows},null,2));
