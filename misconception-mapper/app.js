import { analyzeAttempt, analyzeRetry } from './core/analyze.js';

const $ = id => document.getElementById(id);
let currentSession = null;

$('analyze').addEventListener('click', async () => {
  const result = await analyzeAttempt({
    problem: $('problem').value,
    attempt: $('attempt').value,
    concept: $('concept').value
  });
  currentSession = result.session;
  $('result').hidden = false;
  $('diagnosis').textContent = result.diagnosis.label;
  $('reason').textContent = `${result.diagnosis.confidenceLabel}. ${result.diagnosis.reason}`;
  $('hint').textContent = result.hint;
  $('retry-state').textContent = '';
});

$('check-retry').addEventListener('click', () => {
  if (!currentSession) return;
  currentSession = analyzeRetry(currentSession, $('retry').value);
  const map = {
    improved: 'Improved — the previous misconception pattern was not detected in this retry.',
    'same pattern': 'Same pattern — use the hint and try one more step.',
    uncertain: 'Uncertain — add one intermediate step so the pattern can be checked safely.'
  };
  $('retry-state').textContent = map[currentSession.retryOutcome.status] ?? map.uncertain;
});
