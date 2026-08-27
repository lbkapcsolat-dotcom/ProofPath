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
    const producer = typeof document.modelContext?.registerTool === "function";
    const tester = navigator.modelContextTesting ?? null;
    const testing = !!tester && typeof tester.listTools === "function" && typeof tester.executeTool === "function";
    if (!producer) throw new Error("document.modelContext.registerTool is unavailable");
    if (!testing) throw new Error("navigator.modelContextTesting listTools/executeTool is unavailable");

    const tools = await tester.listTools();
    const serializedTools = JSON.stringify(tools);
    const hasAnalyzeEvidence = serializedTools.includes("analyze_evidence");
    if (!hasAnalyzeEvidence) throw new Error(`analyze_evidence not discovered: ${serializedTools}`);

    const normalRaw = await tester.executeTool(
      "analyze_evidence",
      JSON.stringify({ claim: "Iron is a metal.", evidence: "Iron is classified as a metal." })
    );
    const blockedRaw = await tester.executeTool(
      "analyze_evidence",
      JSON.stringify({ claim: "Iron is a metal.", evidence: "" })
    );

    return {
      producer,
      testing,
      tools,
      normalRaw: String(normalRaw),
      blockedRaw: String(blockedRaw),
    };
  });

  assert.equal(result.producer, true);
  assert.equal(result.testing, true);
  assert.match(result.normalRaw, /SUPPORTED/);
  assert.match(result.blockedRaw, /BLOCK|Add evidence first/);
  console.log(JSON.stringify({ status: "PASS_WEBMCP_BROWSER_RUNTIME", ...result }, null, 2));
} finally {
  await browser.close();
}
