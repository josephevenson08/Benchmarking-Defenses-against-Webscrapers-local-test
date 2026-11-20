// Runs Lighthouse several times on each page of a served condition and keeps the median of each measure
// (midterm §5 "User cost": "Lighthouse runs 5 times per page and I take the median"; D70: performance score,
// FCP, LCP and TTI, as WebCloak reports them). Called by measurement/user_cost.py.
//
//   node measurement/lighthouse.mjs --base http://127.0.0.1:3200 --paths /,/products/p1 [--runs 5] [--json out.json]
//
// Lighthouse's default settings are used (mobile form factor, simulated throttling), only the performance
// category. WebCloak does not say which settings it used. One headless Chromium is started for all the runs;
// Lighthouse resets storage before each run. The browser comes from CHROME_PATH or --chrome-path; user_cost.py
// passes Playwright's Chromium, so no separate Chrome install is needed.
import fs from "node:fs";
import { parseArgs } from "node:util";
import { pathToFileURL } from "node:url";

export const MEASURES = {
  score: (lhr) => (lhr.categories.performance.score === null ? null : lhr.categories.performance.score * 100),
  fcp_ms: (lhr) => lhr.audits["first-contentful-paint"]?.numericValue ?? null,
  lcp_ms: (lhr) => lhr.audits["largest-contentful-paint"]?.numericValue ?? null,
  tti_ms: (lhr) => lhr.audits["interactive"]?.numericValue ?? null,
  tbt_ms: (lhr) => lhr.audits["total-blocking-time"]?.numericValue ?? null,
  cls: (lhr) => lhr.audits["cumulative-layout-shift"]?.numericValue ?? null,
};

export function median(values) {
  const v = values.filter((x) => typeof x === "number" && Number.isFinite(x)).sort((a, b) => a - b);
  if (v.length === 0) return null;
  const mid = Math.floor(v.length / 2);
  return v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
}

// {measure: median over the runs} for one page.
export function medians(runs) {
  return Object.fromEntries(Object.keys(MEASURES).map((k) => [k, median(runs.map((r) => r[k]))]));
}

export function measuresOf(lhr) {
  return Object.fromEntries(Object.entries(MEASURES).map(([k, f]) => [k, f(lhr)]));
}

async function main() {
  const { values } = parseArgs({
    options: {
      base: { type: "string" },
      paths: { type: "string" },
      runs: { type: "string", default: "5" },
      json: { type: "string" },
      "chrome-path": { type: "string" },
    },
  });
  if (!values.base || !values.paths) {
    console.error("Usage: node measurement/lighthouse.mjs --base <url> --paths <p1,p2,...> [--runs 5] [--json out.json]");
    process.exit(2);
  }
  const { default: lighthouse } = await import("lighthouse");
  const chromeLauncher = await import("chrome-launcher");
  const flags = ["--headless=new"];
  if (process.platform === "linux") flags.push("--no-sandbox");
  const chrome = await chromeLauncher.launch({ chromePath: values["chrome-path"] || process.env.CHROME_PATH, chromeFlags: flags });
  const runs = Number(values.runs);
  const report = { lighthouse_version: null, settings: null, runs_per_page: runs, pages: [] };
  try {
    for (const path of values.paths.split(",")) {
      const url = new URL(path, values.base).href;
      const results = [];
      for (let i = 0; i < runs; i++) {
        const result = await lighthouse(url, { port: chrome.port, onlyCategories: ["performance"], output: "json", logLevel: "error" });
        report.lighthouse_version ??= result.lhr.lighthouseVersion;
        report.settings ??= { formFactor: result.lhr.configSettings.formFactor, throttlingMethod: result.lhr.configSettings.throttlingMethod };
        results.push(measuresOf(result.lhr));
      }
      const m = medians(results);
      report.pages.push({ path, runs: results, median: m });
      console.log(`${path.padEnd(16)} score ${m.score}  FCP ${Math.round(m.fcp_ms)} ms  LCP ${Math.round(m.lcp_ms)} ms  TTI ${Math.round(m.tti_ms)} ms  (median of ${runs})`);
    }
  } finally {
    await chrome.kill();
  }
  if (values.json) fs.writeFileSync(values.json, JSON.stringify(report, null, 2) + "\n");
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) await main();
