export function evaluateRetry(previousDiagnosis, retryFeatures) {
  if (previousDiagnosis?.id === 'sign_handling') {
    if (retryFeatures.flags.canonicalCorrectFifteen && retryFeatures.flags.canonicalCorrectFive) return 'improved';
    if (retryFeatures.flags.canonicalWrongTwentyFive) return 'same_pattern';
  }
  if (previousDiagnosis?.id === 'equilibrium_vs_stability') {
    if (!retryFeatures.flags.assertsAutomaticStability && retryFeatures.flags.mentionsEquilibrium) return 'improved';
    if (retryFeatures.flags.assertsAutomaticStability) return 'same_pattern';
  }
  return 'uncertain';
}
