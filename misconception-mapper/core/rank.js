import { MISCONCEPTIONS } from './taxonomy.js';

function baseScore(id, features) {
  const f = features.flags;
  switch (id) {
    case 'sign_handling':
      return f.canonicalPlusFiveToTwenty && f.canonicalWrongTwentyFive ? 1 : 0;
    case 'equilibrium_vs_stability':
      return f.mentionsEquilibrium && f.assertsAutomaticStability ? 1 : 0;
    case 'velocity_vs_acceleration':
      return f.mentionsVelocity && f.mentionsAcceleration ? 0.45 : 0;
    case 'insufficient_evidence':
      return f.containsInstructionLikeText ? 0.2 : 0;
    default:
      return 0;
  }
}

export function rankMisconceptions(features) {
  const scored = MISCONCEPTIONS
    .filter(item => item.id !== 'unknown')
    .map(item => {
      const raw = baseScore(item.id, features);
      return { id: item.id, score: raw, confidence: Math.min(item.confidenceCeiling, raw * item.confidenceCeiling) };
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score || b.confidence - a.confidence || a.id.localeCompare(b.id));

  if (scored.length === 0) {
    return [{ id: 'unknown', score: 0, confidence: 0.4 }];
  }
  return scored;
}
