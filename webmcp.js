export function registerProofPathWebMCP(analyze, modelContext = globalThis?.document?.modelContext ?? null) {
  if (!modelContext || typeof modelContext.registerTool !== "function") return false;

  modelContext.registerTool({
    name: "analyze_evidence",
    description: "Analyze whether supplied evidence supports, contradicts, or is insufficient for a claim. Educational use only; this is not a truth detector or scientific validator.",
    inputSchema: {
      type: "object",
      properties: {
        claim: { type: "string", description: "The claim to assess." },
        evidence: { type: "string", description: "The evidence supplied for that claim." }
      },
      required: ["claim", "evidence"],
      additionalProperties: false
    },
    execute: async ({ claim = "", evidence = "" }) => analyze(String(claim), String(evidence))
  });

  return true;
}
