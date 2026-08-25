import assert from "node:assert/strict";
import {trainSoftmax,predict,extractFeatures} from "./model.js";
import {EARTH_TRAINING_SET,EARTH_HOLDOUT_SET} from "./earth-data.js";
import {nextEvidenceNeeded} from "./app.js";

const model=trainSoftmax(EARTH_TRAINING_SET);
let correct=0; const rows=[];
for(const ex of EARTH_HOLDOUT_SET){
  const p=predict(model,ex.claim,ex.evidence);
  rows.push({category:ex.category,expected:ex.label,predicted:p.label,claim:ex.claim,probabilities:p.probabilities});
  if(p.label===ex.label) correct++;
}
assert.equal(EARTH_TRAINING_SET.length,32,"Expected 32 Earth training pairs");
assert.equal(EARTH_HOLDOUT_SET.length,10,"Expected 10 Earth holdout pairs");
assert.equal(correct,10,`Expected 10/10 fixed Earth holdout result, got ${correct}/10`);
assert.equal(extractFeatures("Methane is a greenhouse gas.","Methane is classified as a greenhouse gas.").length,12);
assert.match(nextEvidenceNeeded("INSUFFICIENT","Water"),/missing baseline|comparison group|time window|scale|measured outcome/i);
console.log(JSON.stringify({correct,total:EARTH_HOLDOUT_SET.length,training_pairs:EARTH_TRAINING_SET.length,rows},null,2));
