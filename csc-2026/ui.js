const claimEl = document.getElementById('claim');
const evidenceEl = document.getElementById('evidence');
const resultEl = document.getElementById('result');

document.getElementById('assess').addEventListener('click', () => {
  const out = window.SchoolEvidenceCoach.assessEvidence({
    claim: claimEl.value,
    evidence: evidenceEl.value,
    assignmentMode: true
  });
  resultEl.innerHTML = `
    <h2>${out.verdict}</h2>
    <p><strong>Match signal:</strong> ${out.confidence}%</p>
    <p>${out.reason}</p>
    <p><strong>Next evidence step:</strong> ${out.nextStep}</p>
    <p class="muted">${out.assignmentHint || ''}</p>
  `;
});