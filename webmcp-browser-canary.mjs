import assert from "node:assert/strict";
import puppeteer from "puppeteer-core";

const executablePath = process.env.CHROME_PATH || "/usr/bin/google-chrome";
const browser = await puppeteer.launch({
  executablePath,
  headless: false,
  args: [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--enable-experimental-web-platform-features",
    "--enable-blink-features=WebMCP",
  ],
});

try {
  const page = await browser.newPage();
  await page.goto("http://127.0.0.1:8000", { waitUntil: "networkidle0" });

  const result = await page.evaluate(async () => {
    const context = document.modelContext ?? null;
    const producer = !!context && typeof context.registerTool === "function";
    const discovery = !!context && typeof context.getTools === "function";
    const execution = !!context && typeof context.executeTool === "function";

    if (!producer) throw new Error("document.modelContext.registerTool is unavailable");
    if (!discovery || !execution) {
      throw new Error("document.modelContext getTools/executeTool is unavailable");
    }

    const tools = await context.getTools();
    const analyzeEvidence = tools.find((candidate) => candidate?.name === "analyze_evidence");
    if (!analyzeEvidence) {
      throw new Error(`analyze_evidence not discovered: ${JSON.stringify(tools.map((tool) => tool?.name))}`);
    }

    const normalRaw = await context.executeTool(
      analyzeEvidence,
      JSON.stringify({ claim: "Iron is a metal.", evidence: "Iron is classified as a metal." })
    );
    const blockedRaw = await context.executeTool(
      analyzeEvidence,
      JSON.stringify({ claim: "Iron is a metal.", evidence: "" })
    );

    return {
      producer,
      discovery,
      execution,
      toolNames: tools.map((tool) => tool?.name),
      normalRaw: String(normalRaw),
      blockedRaw: String(blockedRaw),
    };
  });

  assert.equal(result.producer, true);
  assert.equal(result.discovery, true);
  assert.equal(result.execution, true);
  assert.ok(result.toolNames.includes("analyze_evidence"));
  assert.match(result.normalRaw, /SUPPORTED/);
  assert.match(result.blockedRaw, /BLOCK|Add evidence first/);
  console.log(JSON.stringify({ status: "PASS_WEBMCP_BROWSER_RUNTIME", ...result }, null, 2));
} finally {
  await browser.close();
}
