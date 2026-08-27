# ProofPath — WebMCP Challenge Submission Copy

## Submitter Type
Team of Individuals

## Country
Hungary

## App Status
Existing

## Existing-project challenge-period update
ProofPath existed before the WebMCP Challenge submission period. After the submission period began, we added a new WebMCP layer that exposes the existing bounded evidence-analysis function as a structured `analyze_evidence` tool. The challenge-period delta also includes a dedicated WebMCP adapter contract test, fail-closed behavior for missing analysis input, challenge-specific documentation, an open-source license, a live deployment, full regression CI, and a real headed-Chrome WebMCP runtime canary.

## Live URL
https://elastic-cloud-7bddb2h.shipstatic.com

## Public repository
https://github.com/lbkapcsolat-dotcom/ProofPath/tree/webmcp-challenge

## Testing instructions
1. Open the live URL in a WebMCP-capable client.
2. Confirm that the page exposes the `analyze_evidence` tool.
3. Invoke it with:
   - claim: `Iron is a metal.`
   - evidence: `Iron is classified as a metal.`
4. Confirm a bounded evidence-classification result is returned.
5. Invoke the same tool with blank evidence and confirm the analysis path fails closed rather than producing a confident verdict.

The visual form remains usable when WebMCP is unavailable.

## Which agents/clients did you test your WebMCP tools with?
Google Chrome 151.0.7922.173 in a headed Xvfb-backed GitHub Actions browser session with WebMCP enabled. The WebMCP testing interface discovered `analyze_evidence` and invoked it successfully.

Runtime readback:
- discovered tool: `analyze_evidence`
- normal invocation: `status=READY`, `label=SUPPORTED`, claim ceiling `EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`
- fail-closed invocation with blank evidence: `status=BLOCK`, message `Add evidence first.`
- browser canary run: `33053336003` — success
- full regression run on the same commit: `33053336059` — success

## Which AI tools were leveraged?
ChatGPT was used for implementation assistance, test design, documentation, and submission preparation. GitHub Actions was used for automated regression and real-browser runtime verification. Final project claims are limited to behavior supported by repository, CI, live-host, and browser runtime evidence.

## Learning level
Significant

## Career AI value
Yes

## Main description

### What ProofPath does
ProofPath is an educational evidence-reasoning tool. A person supplies a claim and a piece of evidence; the app classifies the relationship as **SUPPORTED**, **CONTRADICTED**, or **INSUFFICIENT**. It deliberately does not present itself as a truth detector or scientific validator.

### Why WebMCP is a strong fit
Before the WebMCP extension, ProofPath could only be used through its visual form. The new WebMCP layer exposes the same bounded evidence-analysis capability as a structured tool named `analyze_evidence`. This allows an agent to use the app through an explicit contract instead of guessing how to manipulate the visual interface.

The human-facing UI and agent-facing tool do not maintain separate verdict logic. Both call the same `analyze(claim, evidence)` function, preserving the same claim ceiling and fail-closed behavior.

### Better human + agent experience
A person can inspect or enter evidence through the normal UI while an agent can call the same underlying capability directly. The agent receives a structured bounded classification and probabilities that can be incorporated into a larger learning workflow without changing what the tool claims to know.

### WebMCP implementation
The challenge-period adapter registers `analyze_evidence` through `document.modelContext.registerTool`. Its schema requires `claim` and `evidence` strings and rejects additional properties. The execute handler delegates directly to the existing ProofPath `analyze()` function. If WebMCP is unavailable, ProofPath remains a functional ordinary web app.

### Verification
The WebMCP branch contains the original model and UI tests plus a dedicated adapter contract test. GitHub Actions runs the full regression suite and a separate headed-Chrome WebMCP canary. Chrome 151 discovered and invoked the real `analyze_evidence` tool, including a fail-closed blank-evidence case.

### Claim ceiling
`EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`

ProofPath is not a truth detector, scientific validator, medical/legal decision tool, or general automatic fact-checking service.

## Video URL
READY_TO_RECORD — runtime evidence gate passed; final <3-minute public YouTube URL still required.
