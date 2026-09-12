const assert=require('node:assert/strict');
const {classify}=require('./coach.js');

assert.equal(classify('School garden reduced cafeteria food waste','School garden project reduced cafeteria food waste by 18 percent').label,'SUPPORTED');
assert.equal(classify('School garden reduced cafeteria food waste','The school garden did not reduce cafeteria food waste').label,'CONTRADICTED');
assert.equal(classify('School garden reduced cafeteria food waste','Students reported liking outdoor classes').label,'INSUFFICIENT');
assert.equal(classify('','some evidence').label,'INSUFFICIENT');

// Directional-polarity regressions: semantically aligned decrease language must support,
// while opposite-direction increase language must contradict.
assert.equal(
  classify('School garden reduced cafeteria food waste','Cafeteria food waste decreased after the school garden project').label,
  'SUPPORTED'
);
assert.equal(
  classify('School garden reduced cafeteria food waste','Cafeteria food waste increased after the school garden project').label,
  'CONTRADICTED'
);

console.log('CSC School Evidence Coach: 6/6 PASS');
