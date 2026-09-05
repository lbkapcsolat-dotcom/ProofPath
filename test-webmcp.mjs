import assert from "node:assert/strict";
import { registerProofPathWebMCP } from "./webmcp.js";

let registered = null;
const fakeModelContext = {
  registerTool(definition) {
    registered = definition;
  }
};

const fakeAnalyze = (claim, evidence) => {
  if (!claim.trim()) return { status: "BLOCK", message: "Add a claim first." };
  if (!evidence.trim()) return { status: "BLOCK", message: "Add evidence first." };
  return {
    status: "READY",
    label: "INSUFFICIENT",
    probabilities: { SUPPORTED: 0.1, CONTRADICTED: 0.2, INSUFFICIENT: 0.7 },
    claim_ceiling: "EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY"
  };
};

assert.equal(registerProofPathWebMCP(fakeAnalyze, fakeModelContext), true);
assert.equal(registered.name, "analyze_evidence");
assert.deepEqual(Object.keys(registered.inputSchema.properties), ["claim", "evidence"]);

const ready = await registered.execute({ claim: "A claim", evidence: "Some evidence" });
assert.equal(ready.status, "READY");
assert.equal(ready.label, "INSUFFICIENT");
assert.equal(ready.claim_ceiling, "EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY");

const blocked = await registered.execute({ claim: "", evidence: "Some evidence" });
assert.equal(blocked.status, "BLOCK");
assert.equal(blocked.message, "Add a claim first.");

assert.equal(registerProofPathWebMCP(fakeAnalyze, null), false);
console.log("PASS webmcp adapter contract");
