import { extractFeatures } from './features.js';
import { rankMisconceptions } from './rank.js';
import { selectDiagnosis } from './diagnosis.js';
import { buildHint } from './hints.js';
import { evaluateRetry } from './retry.js';
import { createSession, applyDiagnosis, applyRetry } from './session.js';
import { rerankWithOptionalModel } from './modelAdapter.js';

const SUPPORTED = new Set(['', 'algebra', 'physics']);

export async function analyzeAttempt({ problem = '', attempt = '', concept = '', model = { enabled:false } } = {}) {
  const normalizedConcept = String(concept ?? '').trim().toLowerCase();
  const baseSession = createSession({ problem, attempt, concept: normalizedConcept });

  if (!String(attempt ?? '').trim()) {
    const diagnosis = { id:'unknown', label:'Need an attempt', status:'input_required', confidence:0, confidenceLabel:'No diagnosis', reason:'Enter an attempted answer before requesting a diagnosis.' };
    const hint = 'Can you show your attempted step first?';
    return { features:null, candidates:[], diagnosis, hint, session:applyDiagnosis(baseSession, diagnosis, hint) };
  }

  if (!SUPPORTED.has(normalizedConcept)) {
    const diagnosis = { id:'unknown', label:'Unsupported concept', status:'unsupported', confidence:0, confidenceLabel:'Unsupported domain', reason:'V1 supports only introductory algebra and physics.' };
    const hint = 'Can you choose algebra or physics for this prototype?';
    return { features:null, candidates:[], diagnosis, hint, session:applyDiagnosis(baseSession, diagnosis, hint) };
  }

  const features = extractFeatures(problem, attempt, normalizedConcept);
  const ranked = rankMisconceptions(features);
  const candidates = await rerankWithOptionalModel(ranked, model);
  const diagnosis = selectDiagnosis(candidates);
  const hint = buildHint(diagnosis);
  const session = applyDiagnosis(baseSession, diagnosis, hint);
  return { features, candidates, diagnosis, hint, session };
}

export function analyzeRetry(session, retry) {
  const retryOutcome = evaluateRetry({
    diagnosisId: session?.diagnosis?.id ?? 'unknown',
    problem: session?.problem ?? '',
    previousAttempt: session?.attempt ?? '',
    retry,
    concept: session?.concept ?? ''
  });
  return applyRetry(session, retry, retryOutcome);
}
