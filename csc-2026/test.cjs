const assert=require('node:assert/strict');
const {classify}=require('./coach.js');
assert.equal(classify('School garden reduced cafeteria food waste','School garden project reduced cafeteria food waste by 18 percent').label,'SUPPORTED');
assert.equal(classify('School garden reduced cafeteria food waste','The school garden did not reduce cafeteria food waste').label,'CONTRADICTED');
assert.equal(classify('School garden reduced cafeteria food waste','Students reported liking outdoor classes').label,'INSUFFICIENT');
assert.equal(classify('','some evidence').label,'INSUFFICIENT');
console.log('CSC School Evidence Coach: 4/4 PASS');