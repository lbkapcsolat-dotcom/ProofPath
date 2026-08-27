export type AssessmentLabel = 'SUPPORTED' | 'CONTRADICTED' | 'INSUFFICIENT';

export type AssessmentResult = {
  label: AssessmentLabel;
  confidence: number;
  rationale: string;
};

const NEGATIONS = ['not', 'never', 'no ', "doesn't", "isn't", "wasn't", 'cannot', "can't"];

function tokens(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .replace(/[^a-z0-9\s.-]/g, ' ')
      .split(/\s+/)
      .filter((token) => token.length > 2),
  );
}

function hasNegation(text: string): boolean {
  const lower = text.toLowerCase();
  return NEGATIONS.some((cue) => lower.includes(cue));
}

export function assessEvidence(claim: string, evidence: string): AssessmentResult {
  const claimTokens = tokens(claim);
  const evidenceTokens = tokens(evidence);

  if (claimTokens.size === 0 || evidenceTokens.size === 0) {
    return {
      label: 'INSUFFICIENT',
      confidence: 0.5,
      rationale: 'A claim and a concrete evidence statement are both required.',
    };
  }

  const overlap = [...claimTokens].filter((token) => evidenceTokens.has(token)).length;
  const overlapRatio = overlap / Math.max(claimTokens.size, 1);
  const negationMismatch = hasNegation(claim) !== hasNegation(evidence);

  if (overlapRatio >= 0.45 && negationMismatch) {
    return {
      label: 'CONTRADICTED',
      confidence: Math.min(0.9, 0.6 + overlapRatio * 0.3),
      rationale: 'The evidence discusses much of the same content but reverses a key polarity cue.',
    };
  }

  if (overlapRatio >= 0.55) {
    return {
      label: 'SUPPORTED',
      confidence: Math.min(0.9, 0.55 + overlapRatio * 0.35),
      rationale: 'The evidence has substantial lexical alignment with the claim without an obvious contradiction cue.',
    };
  }

  return {
    label: 'INSUFFICIENT',
    confidence: Math.max(0.5, 0.72 - overlapRatio * 0.25),
    rationale: 'The evidence does not overlap enough with the claim to justify a stronger conclusion.',
  };
}
