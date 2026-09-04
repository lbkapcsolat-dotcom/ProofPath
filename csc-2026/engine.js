const VERDICTS = Object.freeze({
  SUPPORTED: 'SUPPORTED',
  CONTRADICTED: 'CONTRADICTED',
  INSUFFICIENT: 'INSUFFICIENT'
});

function normalize(text='') {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

function tokens(text='') {
  return new Set(normalize(text).split(' ').filter(w => w.length >= 4));
}

function overlap(a, b) {
  const A = tokens(a), B = tokens(b);
  if (!A.size || !B.size) return 0;
  let hit = 0;
  for (const x of A) if (B.has(x)) hit++;
  return hit / Math.max(A.size, 1);
}

function hasNegation(text='') {
  return /\b(no|not|never|without|cannot|can't|doesn't|isn't|aren't|didn't|won't)\b/i.test(text);
}

function assessEvidence({claim='', evidence='', assignmentMode=true}={}) {
  const c = claim.trim();
  const e = evidence.trim();
  if (!c || !e) {
    return {
      verdict: VERDICTS.INSUFFICIENT,
      confidence: 0,
      ceiling: 'EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY',
      reason: 'A claim and evidence passage are both required.',
      nextStep: 'Add a specific evidence passage that directly addresses the claim.'
    };
  }

  const ov = overlap(c, e);
  const negMismatch = hasNegation(c) !== hasNegation(e);
  let verdict = VERDICTS.INSUFFICIENT;
  let reason = 'The evidence does not directly address enough of the claim to justify support or contradiction.';
  let nextStep = 'Find a source passage that directly addresses the key terms and relationship in the claim.';

  if (ov >= 0.5 && negMismatch) {
    verdict = VERDICTS.CONTRADICTED;
    reason = 'The evidence substantially overlaps the claim but reverses an important assertion.';
    nextStep = 'Check the source context and whether the evidence is authoritative for this exact claim.';
  } else if (ov >= 0.5) {
    verdict = VERDICTS.SUPPORTED;
    reason = 'The evidence directly overlaps the main content of the claim without an obvious contradiction signal.';
    nextStep = 'Verify source quality and citation details before using the claim in an assignment.';
  }

  return {
    verdict,
    confidence: Math.round(Math.min(1, ov) * 100),
    ceiling: 'EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY',
    reason,
    nextStep,
    assignmentHint: assignmentMode ? 'Use this as a reasoning aid, not as a substitute for teacher feedback or source verification.' : undefined
  };
}

if (typeof module !== 'undefined') module.exports = {VERDICTS, normalize, overlap, assessEvidence};
if (typeof window !== 'undefined') window.SchoolEvidenceCoach = {VERDICTS, normalize, overlap, assessEvidence};