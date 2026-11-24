// Writes lighthouse/summary.md after a Lighthouse run on the live page.
// Usage: node perf/live-summary.mjs <live-url> <lighthouse-json> <commit-sha>
// It also downloads the live page and compares its sold-out buttons with the stock file.
import { readFileSync, writeFileSync } from "node:fs";

const [url, reportPath, sha] = process.argv.slice(2);
const report = JSON.parse(readFileSync(reportPath, "utf8"));
const rows = JSON.parse(readFileSync("data/nike_pegasus_size_stock.json", "utf8"))
  .sort((a, b) => a.display_order - b.display_order);
const html = await (await fetch(url)).text();

const fmt = (v) => String(Number(v));
const a = report.audits;
const score = Math.round(report.categories.performance.score * 100);
const s = report.configSettings;

// Sold-out buttons as the live page renders them.
const liveSold = [...html.matchAll(/data-testid="size-button-sold-out"[^>]*?data-sku="([^"]+)"/g)].map((m) => m[1]);
const liveAvailable = [...html.matchAll(/data-testid="size-button"[^>]*?data-sku="([^"]+)"/g)].map((m) => m[1]);
const fileSold = rows.filter((r) => r.stock_status === "sold_out" || !r.in_stock);
const match =
  liveSold.length === fileSold.length && fileSold.every((r) => liveSold.includes(r.sku)) &&
  liveSold.length + liveAvailable.length === rows.length;

const soldRows = fileSold
  .map((r) => `| ${fmt(r.size_us_men)} | ${fmt(r.size_us_women)} | ${r.size_eu} | \`${r.sku}\` | ${r.stock_quantity} | ${liveSold.includes(r.sku) ? "Yes" : "**No**"} |`)
  .join("\n");

const md = `# Lighthouse report: live page

- **URL tested:** ${report.finalDisplayedUrl}
- **Run at:** ${report.fetchTime}
- **Commit:** \`${sha.slice(0, 7)}\`
- **Lighthouse:** ${report.lighthouseVersion}, ${s.formFactor}, ${s.throttlingMethod} throttling: ${s.throttling.rttMs} ms RTT, ${s.throttling.throughputKbps} Kbps (Slow 4G), ${s.throttling.cpuSlowdownMultiplier}x CPU slowdown, ${s.screenEmulation.width} × ${s.screenEmulation.height} at ${s.screenEmulation.deviceScaleFactor}x

| Metric | Result |
| --- | --- |
| Performance score | **${score}** |
| First contentful paint | ${a["first-contentful-paint"].displayValue} |
| Largest contentful paint | ${a["largest-contentful-paint"].displayValue} |
| Total blocking time | ${a["total-blocking-time"].displayValue} |
| Cumulative layout shift | ${a["cumulative-layout-shift"].displayValue} |
| Speed index | ${a["speed-index"].displayValue} |

Full report: [mobile-slow4g.html](mobile-slow4g.html) (open the raw file or download it) · data: [mobile-slow4g.json](mobile-slow4g.json)

## Sold-out sizes: live page vs stock file

Live page has ${liveSold.length} sold-out buttons and ${liveAvailable.length} other size buttons (${liveSold.length + liveAvailable.length} in total). The stock file has ${fileSold.length} sold-out sizes out of ${rows.length}. **${match ? "They match." : "They do not match."}**

| US Men's | US Women's | EU | SKU | Pairs in file | Sold-out button on live page |
| --- | --- | --- | --- | --- | --- |
${soldRows}
`;
writeFileSync("lighthouse/summary.md", md);
console.log(md);
