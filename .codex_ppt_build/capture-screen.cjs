const { chromium } = require("C:/Users/Akito/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  await page.goto("http://127.0.0.1:8765/", { waitUntil: "networkidle" });
  const frame = page.frameLocator("iframe");
  await frame.locator("#self-review-app .mobile-section").evaluate(el => { el.style.display = "none"; });
  await frame.locator("#self-review-app").screenshot({ path: "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app/.codex_ppt_build/self-review-desktop.png", animations: "disabled" });
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
