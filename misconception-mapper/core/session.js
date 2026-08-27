export function createSession({ problem = '', attempt = '', concept = '' } = {}) {
  return { problem, attempt, concept, diagnosis: null, hint: '', retry: '', retryOutcome: null };
}
export function applyDiagnosis(session, diagnosis, hint) {
  return { ...session, diagnosis, hint };
}
export function applyRetry(session, retry, retryOutcome) {
  return { ...session, retry, retryOutcome };
}
