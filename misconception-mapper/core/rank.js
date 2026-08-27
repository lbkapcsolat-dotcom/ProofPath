import { getMisconception } from './taxonomy.js';

function capped(id, raw, evidence) {
  const ceiling = getMisconception(id)?.confidenceCeiling ?? 0.4;
  return { id, score: Math.min(raw, ceiling), evidence };
}

export function rankMisconceptions(features) {
  const { flags } = features;
  const candidates = [];
  if (flags.canonicalPlusFiveToTwenty && flags.canonicalWrongTwentyFive) candidates.push(capped('sign_handling', 0.88, ['+5 became +5 instead of being undone']));
  if (flags.mentionsEquilibrium && flags.assertsAutomaticStability) candidates.push(capped('equilibrium_vs_stability', 0.84, ['equilibrium was treated as automatically stable']));
  if (flags.mentionsVelocity && flags.mentionsAcceleration) candidates.push(capped('velocity_vs_acceleration', 0.62, ['both velocity and acceleration terms appear']));
  if (candidates.length === 0) candidates.push(capped('unknown', 0.4, ['no bounded rule matched confidently']));
  return candidates.sort((a, b) => b.score - a.score);
}
