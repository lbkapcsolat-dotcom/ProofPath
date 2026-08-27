import { analyzeAttempt, analyzeRetry } from './core/analyze.js';
import { createSession, recordDiagnosis, recordRetry } from './core/session.js';

let state = createSession();
const $ = id => document.getElementById(id);

$('analyze').addEventListener('click', async () => {
  const problem = $('problem').value;
  const attempt = $('attempt').value;
  const concept = $('concept').value;
  const result = await analyzeAttempt({ problem, attempt, concept });
  state = recordDiagnosis(state, { problem, attempt, diagnosis: result.diagnosis, hint: result.hint });
  $('diagnosis').textContent = `${result.diagnosis.label} — ${result.diagnosis.confidenceText}`;
  $('why').textContent = result.diagnosis.why;
  $('hint').textContent = result.hint.text;
});

$('retryButton').addEventListener('click', () => {
  if (!state.diagnosis) {
    $('learningState').textContent = 'Map an attempt before checking a retry.';
    return;
  }
  const retry = $('retry').value;
  const { outcome } = analyzeRetry({ problem: state.problem, previousDiagnosis: state.diagnosis, retry, concept: $('concept').value });
  state = recordRetry(state, retry, outcome);
  const labels = {
    improved: 'Improved — previous misconception pattern not detected in this retry.',
    same_pattern: 'Same pattern — try the Socratic hint once more.',
    uncertain: 'Uncertain — show one more intermediate step.'
  };
  $('learningState').textContent = labels[outcome];
});
