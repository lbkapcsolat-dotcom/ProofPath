
import assert from "node:assert/strict";
import fs from "node:fs";
const html=fs.readFileSync("./index.html","utf8"), app=fs.readFileSync("./app.js","utf8");
for(const s of ['id="claim"','id="evidence"','id="exampleSelect"','id="modelStatus"','EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY']) assert.match(html,new RegExp(s));
assert.match(app,/trainSoftmax/);assert.match(app,/HOLDOUT_SET/);assert.match(app,/export function analyze/);
console.log("PASS: submission UI static checks");
