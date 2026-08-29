export function lockAuthoritativeVerdict(authoritative, gemini = {}) {
  if (!authoritative || authoritative.status !== 'READY') {
    return { status: 'BLOCK', message: 'Authoritative classifier result required before Gemini explanation.' };
  }
  return {
    status: 'READY',
    label: authoritative.label,
    probabilities: authoritative.probabilities,
    explanation: typeof gemini.explanation === 'string' ? gemini.explanation : '',
    nextEvidenceStep: typeof gemini.nextEvidenceStep === 'string' ? gemini.nextEvidenceStep : ''
  };
}

export function buildGeminiPrompt({ claim, evidence, authoritative }) {
  return `You are an educational explanation layer for ProofPath.\n\nThe authoritative classifier verdict is ${authoritative.label}. You must not change, replace, strengthen, or weaken that verdict or its probabilities.\n\nClaim: ${claim}\nEvidence: ${evidence}\n\nExplain in plain student-friendly language why the supplied evidence may be limited under the authoritative verdict, then suggest one next evidence-gathering step. Do not act as a truth detector, medical/legal/scientific validator, or grading authority. Return educational guidance only.`;
}
