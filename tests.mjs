import assert from "node:assert/strict";
import {trainSoftmax,predict,extractFeatures} from "./model.js";
import {EARTH_TRAINING_SET,EARTH_HOLDOUT_SET} from "./earth-data.js";
import {detectEarthCategory,nextEvidenceNeeded,evidenceContextCoverage} from "./earth-logic.js";

const model=trainSoftmax(EARTH_TRAINING_SET);
let correct=0;
for(const ex of EARTH_HOLDOUT_SET){
  const p=predict(model,ex.claim,ex.evidence);
  if(p.label===ex.label) correct++;
}
assert.equal(EARTH_TRAINING_SET.length,32,"Expected 32 Earth training pairs");
assert.equal(EARTH_HOLDOUT_SET.length,10,"Expected 10 Earth holdout pairs");
assert.equal(correct,10,`Expected 10/10 fixed Earth holdout result, got ${correct}/10`);
assert.equal(extractFeatures("Methane is a greenhouse gas.","Methane is classified as a greenhouse gas.").length,12);
assert.equal(detectEarthCategory("Rain gardens capture runoff.","Stormwater runoff can be absorbed."),"Water");
assert.match(nextEvidenceNeeded("INSUFFICIENT","Water"),/missing baseline|comparison group|time window|scale|measured outcome/i);

const sparse=evidenceContextCoverage(
  "A bike lane reduced traffic pollution citywide.",
  "Pollution was lower after the bike lane opened."
);
assert.deepEqual(sparse,{
  baseline:"MISSING",
  comparison:"MISSING",
  time_window:"MISSING",
  spatial_scale:"MISSING",
  measured_outcome:"PRESENT",
  source_provenance:"MISSING"
});

const explicitNA=evidenceContextCoverage(
  "A site-specific sensor reading is reported.",
  "Baseline not applicable. Comparison not applicable. Source: station log. Observed at the site in 2026."
);
assert.equal(explicitNA.baseline,"NOT_APPLICABLE");
assert.equal(explicitNA.comparison,"NOT_APPLICABLE");

const rich=evidenceContextCoverage(
  "A city bike lane reduced roadside pollution.",
  "According to the 2026 city monitoring report, roadside NO2 was measured citywide for six months before and after opening, compared with a reference corridor, and was 12% lower after the intervention."
);
assert.deepEqual(rich,{
  baseline:"PRESENT",
  comparison:"PRESENT",
  time_window:"PRESENT",
  spatial_scale:"PRESENT",
  measured_outcome:"PRESENT",
  source_provenance:"PRESENT"
});

const provenanceOnly=evidenceContextCoverage(
  "Urban air quality improved.",
  "Source: city report, 2026."
);
assert.equal(provenanceOnly.measured_outcome,"MISSING");

console.log(JSON.stringify({status:"PASS",holdout:`${correct}/${EARTH_HOLDOUT_SET.length}`,coverage_tests:4},null,2));
