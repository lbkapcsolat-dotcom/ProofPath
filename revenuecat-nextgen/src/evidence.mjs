const STOPWORDS = new Set(['the','a','an','is','are','was','were','to','of','and','or','in','on','for','with','after','according','some','this','that','be','been']);

function words(text) {
  return String(text).toLowerCase().match(/[a-z0-9]+/g)?.filter((w) => !STOPWORDS.has(w)) ?? [];
}

function hasNegation(text) {
  return /\b(no|not|never|without|cannot|can't|didn't|doesn't|isn't|wasn't|weren't)\b/i.test(text);
}

export function analyzeEvidence(claim, evidence) {
  const c = String(claim ?? '').trim();
  const e = String(evidence ?? '').trim();
  if (!c || !e) {
    return { verdict: 'INSUFFICIENT', reason: 'Both a claim and evidence are required.', nextEvidence: 'Add a concrete claim and a source-backed observation.' };
  }

  const cWords = new Set(words(c));
  const eWords = new Set(words(e));
  const shared = [...cWords].filter((w) => eWords.has(w));
  const overlap = shared.length / Math.max(1, cWords.size);

  if (overlap >= 0.35 && hasNegation(c) !== hasNegation(e)) {
    return { verdict: 'CONTRADICTED', reason: 'The evidence overlaps with the claim but reverses its polarity.', nextEvidence: 'Check the source context, measurement conditions, and whether the negation is material.' };
  }

  if (overlap >= 0.45) {
    return { verdict: 'SUPPORTED', reason: 'The evidence shares the claim’s central terms without an obvious polarity conflict.', nextEvidence: 'Look for an independent source or a stronger baseline to test whether the support generalizes.' };
  }

  return { verdict: 'INSUFFICIENT', reason: 'The evidence does not overlap enough with the claim to support a bounded conclusion.', nextEvidence: 'Find evidence that measures the same subject, outcome, time window, and comparison implied by the claim.' };
}
