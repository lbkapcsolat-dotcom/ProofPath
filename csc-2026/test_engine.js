const assert = require('assert');
const {assessEvidence, VERDICTS} = require('./engine');

const supported = assessEvidence({
  claim:'School gardens improve student science engagement',
  evidence:'A study found school gardens improve student science engagement and classroom participation.'
});
assert.equal(supported.verdict, VERDICTS.SUPPORTED);

const contradicted = assessEvidence({
  claim:'School gardens improve student science engagement',
  evidence:'A study found school gardens do not improve student science engagement.'
});
assert.equal(contradicted.verdict, VERDICTS.CONTRADICTED);

const insufficient = assessEvidence({
  claim:'School gardens improve student science engagement',
  evidence:'The cafeteria changed its lunch menu this year.'
});
assert.equal(insufficient.verdict, VERDICTS.INSUFFICIENT);

const blank = assessEvidence({
  claim:'School gardens improve student science engagement',
  evidence:''
});
assert.equal(blank.verdict, VERDICTS.INSUFFICIENT);
assert.equal(blank.ceiling, 'EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY');

const ceiling = assessEvidence({
  claim:'Homework clubs improve attendance',
  evidence:'Homework clubs improve attendance in this school survey.'
});
assert.equal(ceiling.ceiling, 'EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY');
assert.ok(ceiling.assignmentHint.includes('reasoning aid'));

console.log('PASS 5/5 School Evidence Coach tests');