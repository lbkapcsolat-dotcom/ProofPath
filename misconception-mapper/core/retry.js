import { extractFeatures } from './features.js';

export function evaluateRetry({ diagnosisId, problem, previousAttempt, retry, concept = '' }) {
  if (!retry || diagnosisId === 'unknown') return { status: 'uncertain' };
  const f = extractFeatures(problem, retry, concept);
  if (diagnosisId === 'sign_handling') {
    if (f.flags.canonicalCorrectFifteen && f.flags.canonicalCorrectFive) return { status: 'improved' };
    if (f.flags.canonicalWrongTwentyFive) return { status: 'same pattern' };
  }
  if (diagnosisId === 'equilibrium_vs_stability' && !f.flags.assertsAutomaticStability && f.flags.mentionsEquilibrium) {
    return { status: 'improved' };
  }
  return { status: 'uncertain' };
}
