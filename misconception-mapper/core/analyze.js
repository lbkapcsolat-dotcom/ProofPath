import { extractFeatures } from './features.js';
import { rankMisconceptions } from './rank.js';
import { selectDiagnosis } from './diagnosis.js';
import { buildHint } from './hints.js';
import { evaluateRetry } from './retry.js';
import { rerankWithOptionalModel } from './modelAdapter.js';

const SUPPORTED_CONCEPTS = new Set(['', 'algebra', 'physics']);

export async function analyzeAttempt({ problem, attempt, concept = '' }) {
  const features = extractFeatures(problem, attempt, concept);
  if (features.flags.emptyAttempt) {
    const diagnosis = { status:'need_attempt', id:'unknown', label:'Add an attempt first', confidenceText:'No diagnosis yet', why:'A student attempt is required before pattern matching.' };
    return { diagnosis, hint:buildHint(diagnosis), source:'deterministic' };
  }
  if (!SUPPORTED_CONCEPTS.has(String(concept).toLowerCase())) {
    const diagnosis = { status:'unsupported', id:'unknown', label:'Unsupported concept', confidenceText:'No diagnosis attempted', why:'V1 supports only introductory algebra and physics.' };
    return { diagnosis, hint:buildHint(diagnosis), source:'deterministic' };
  }
  const ranked = rankMisconceptions(features);
  const reranked = await rerankWithOptionalModel(ranked, { problem, attempt, concept });
  const diagnosis = selectDiagnosis(reranked.candidates);
  return { diagnosis, hint:buildHint(diagnosis), source:reranked.source };
}

export function analyzeRetry({ problem, previousDiagnosis, retry, concept = '' }) {
  const retryFeatures = extractFeatures(problem, retry, concept);
  return { outcome:evaluateRetry(previousDiagnosis, retryFeatures) };
}
