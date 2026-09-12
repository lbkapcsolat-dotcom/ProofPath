# ProofPath — WebMCP Challenge Demo Script (<3 minutes)

## Goal
Show a working ProofPath live app, then demonstrate that an agent can call the same bounded evidence-analysis path through WebMCP.

## 0:00–0:20 — Problem and product
On screen: live ProofPath app.

Narration:
“ProofPath is an educational evidence-reasoning tool. A user gives it a claim and evidence, and it classifies the relationship as supported, contradicted, or insufficient. It is deliberately not a truth detector.”

## 0:20–0:45 — Human UI path
On screen: enter a simple claim/evidence pair and run Analyze evidence.

Example:
Claim: `Iron is a metal.`
Evidence: `Iron is classified as a metal.`

Show the returned class and probabilities.

Narration:
“The human interface uses a compact offline classifier and keeps a strict claim ceiling: educational evidence assessment only.”

## 0:45–1:15 — Why WebMCP
On screen: show the WebMCP tool registration in `webmcp.js`.

Narration:
“Before this challenge, ProofPath only exposed this capability through its visual interface. During the challenge period we added a WebMCP tool named `analyze_evidence`. The agent no longer has to guess how to operate the UI; it gets a structured tool with explicit claim and evidence inputs.”

## 1:15–1:55 — Agent invocation
On screen: supported WebMCP client/browser tool list showing `analyze_evidence`, then invoke it with the same example.

Show exact returned result from the real runtime.

Narration:
“The WebMCP tool calls the exact same `analyze()` function as the UI. There is no second verdict engine for agents, so human and agent interactions share the same bounded behavior.”

## 1:55–2:20 — Fail-closed canary
On screen: invoke the tool with missing/blank evidence.

Show the real runtime returning `BLOCK` / missing-evidence response.

Narration:
“We also keep failure conservative. Missing required evidence does not become a confident verdict; the analysis path blocks instead.”

## 2:20–2:40 — Verification
On screen: GitHub Actions WebMCP Regression run and public repository.

Narration:
“The branch includes the original model and UI regressions plus a dedicated WebMCP adapter contract test. The current regression workflow is green.”

## 2:40–2:55 — Close
On screen: live app + repository side by side.

Narration:
“ProofPath demonstrates a small but important WebMCP idea: people and agents can use one transparent, constrained capability through the interface that fits each of them, without duplicating the decision logic.”

## Required capture gate before recording final video
Do not record the final submission video until all are true:
- live URL reachable
- `analyze_evidence` visible in a supported WebMCP browser/client
- one normal invocation read back exactly
- one fail-closed invocation read back exactly
- final CI run on the submitted commit is green

If any item is missing, keep video status HOLD rather than simulating the runtime.