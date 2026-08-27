import { getMisconception } from './taxonomy.js';

function unknownDiagnosis() {
  const item = getMisconception('unknown');
  return {
    id: item.id,
    label: item.label,
    status: 'uncertain',
    confidence: item.confidenceCeiling,
    confidenceLabel: 'Uncertain — need more context',
    reason: 'The available evidence does not support a single bounded misconception pattern.'
  };
}

export function selectDiagnosis(candidates = []) {
  if (!Array.isArray(candidates) || candidates.length === 0) return unknownDiagnosis();
  const [first, second] = candidates;
  if (!first || first.id === 'unknown' || first.confidence < 0.6) return unknownDiagnosis();
  if (second && Math.abs((first.score ?? 0) - (second.score ?? 0)) < 0.1) return unknownDiagnosis();
  const item = getMisconception(first.id);
  if (!item) return unknownDiagnosis();
  return {
    id: item.id,
    label: item.label,
    status: 'likely',
    confidence: Math.min(first.confidence, item.confidenceCeiling),
    confidenceLabel: 'Likely pattern',
    reason: `The submitted steps match bounded signals associated with ${item.label.toLowerCase()}.`
  };
}
