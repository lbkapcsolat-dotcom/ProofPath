# Devpost submission copy — Draft

## Name
ProofPath

## Tagline
Learn what your evidence can actually support.

## What it does
ProofPath is an educational AI/ML tool that teaches evidence reasoning. A learner enters a claim and a piece of evidence. A small offline multiclass ML model classifies the relationship as SUPPORTED, CONTRADICTED, or INSUFFICIENT, then gives a learning prompt about what to check next.

## Why we built it
AI makes answers easy to generate. Evaluating evidence is harder. ProofPath focuses on that missing learning skill.

## How we built it
ProofPath uses a compact three-class softmax-regression model trained from bundled labeled claim–evidence examples. Its feature representation captures overlap, coverage, negation mismatch, numeric mismatch, contradiction cues, uncertainty cues, overclaim cues, and related signals. The app runs offline in the browser with no API key or paid service.

## Accomplishments
- fully offline browser ML
- three evidence classes
- transparent probabilities
- 10/10 on the bundled untouched demo/holdout set
- no paid API or cloud dependency

## Limitations
The model is intentionally small and the benchmark is curated. It is an educational prototype, not a truth detector or general-purpose fact checker.

## Built with
JavaScript, HTML, CSS, multiclass logistic regression / softmax regression
