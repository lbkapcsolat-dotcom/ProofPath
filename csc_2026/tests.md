# CSC 2026 fresh acceptance fixtures

Run these against the event-window Assignment Mode and preserve fail-closed behavior.

1. **Blank evidence** → `INSUFFICIENT`.
2. Claim: `The school library closes at 6 PM on Fridays.` Evidence: `On Fridays the school library closes at 6 PM.` → `SUPPORTED`.
3. Same claim. Evidence: `The school library does not close at 6 PM on Fridays; it closes at 5 PM.` → `CONTRADICTED`.
4. Claim about library hours. Evidence only about cafeteria lunch service → `INSUFFICIENT`.
5. Every output keeps `EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`; no output claims independent truth verification.

These are CSC event-specific acceptance fixtures, not a claim that the lightweight prototype is a semantic entailment benchmark.
