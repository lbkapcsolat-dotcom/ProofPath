function normalize(value) {
  return String(value ?? '').trim().toLowerCase().replace(/\s+/g, ' ');
}

export function extractFeatures(problem, attempt, concept = '') {
  const normalizedProblem = normalize(problem);
  const normalizedAttempt = normalize(attempt);
  const normalizedConcept = normalize(concept);

  return {
    normalizedProblem,
    normalizedAttempt,
    concept: normalizedConcept,
    flags: {
      emptyAttempt: normalizedAttempt.length === 0,
      hasEquation: normalizedProblem.includes('=') || normalizedAttempt.includes('='),
      canonicalPlusFiveToTwenty: normalizedProblem.includes('3x + 5 = 20'),
      canonicalWrongTwentyFive: normalizedAttempt.includes('3x = 25'),
      canonicalCorrectFifteen: normalizedAttempt.includes('3x = 15'),
      canonicalCorrectFive: /x\s*=\s*5(?:\D|$)/.test(normalizedAttempt),
      mentionsEquilibrium: normalizedProblem.includes('equilibrium') || normalizedAttempt.includes('equilibrium'),
      mentionsStable: normalizedProblem.includes('stable') || normalizedAttempt.includes('stable'),
      assertsAutomaticStability: /equilibrium.*(means|is).*stable|every equilibrium.*stable/.test(`${normalizedProblem} ${normalizedAttempt}`),
      mentionsVelocity: normalizedProblem.includes('velocity') || normalizedAttempt.includes('velocity'),
      mentionsAcceleration: normalizedProblem.includes('acceleration') || normalizedAttempt.includes('acceleration'),
      containsInstructionLikeText: /(ignore previous|system prompt|hidden reasoning|chain of thought)/.test(normalizedAttempt)
    }
  };
}
