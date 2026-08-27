export function createSession() {
  return { problem:'', attempt:'', diagnosis:null, hint:null, retry:'', retryOutcome:null };
}
export function recordDiagnosis(state, payload) {
  return { ...state, ...payload };
}
export function recordRetry(state, retry, retryOutcome) {
  return { ...state, retry, retryOutcome };
}
