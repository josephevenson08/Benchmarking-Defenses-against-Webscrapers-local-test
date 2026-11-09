// Compares two folders of page screenshots with pixelmatch and reports, for each
// page, the share of pixels that differ (midterm §2 Measurement, §3: "a short Node
// script reads two PNGs and counts mismatched pixels, which I divide by the
// page's total pixels"). Used for Test 4 (shuffled vs baseline, at most 1%).
//
//   node measurement/pixel_diff.mjs <baseline-dir> <other-dir> [--diff-dir <dir>] [--limit <percent>] [--json <file>]
//
// Screenshots come from measurement/screenshots.py, one PNG per page with the same
// file name in both folders. If two screenshots differ in size (the layout grew or
// shrank), the pixels that exist in only one of them count as different.
// pixelmatch's defaults are used: colour threshold 0.1, anti-aliased pixels ignored.
import fs from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util";
import { pathToFileURL } from "node:url";
import pixelmatch from "pixelmatch";
import pngjs from "pngjs";

const { PNG } = pngjs;
const THRESHOLD = 0.1;

// Copies the top-left width x height part of an image's pixels.
function crop(png, width, height) {
  if (png.width === width && png.height === height) return png.data;
  const out = Buffer.alloc(width * height * 4);
  for (let y = 0; y < height; y++) {
    png.data.copy(out, y * width * 4, y * png.width * 4, y * png.width * 4 + width * 4);
  }
  return out;
}

// Differing pixels between two decoded PNGs, out of the larger canvas.
export function comparePngs(a, b, diffPath) {
  const width = Math.min(a.width, b.width);
  const height = Math.min(a.height, b.height);
  const diff = new PNG({ width, height });
  const overlap = pixelmatch(crop(a, width, height), crop(b, width, height), diff.data, width, height, { threshold: THRESHOLD });
  const total = Math.max(a.width, b.width) * Math.max(a.height, b.height);
  const onlyInOne = total - width * height;
  if (diffPath) fs.writeFileSync(diffPath, PNG.sync.write(diff));
  const mismatched = overlap + onlyInOne;
  return {
    width: [a.width, b.width],
    height: [a.height, b.height],
    mismatched,
    total,
    percent: (100 * mismatched) / total,
  };
}

export function readPng(file) {
  return PNG.sync.read(fs.readFileSync(file));
}

// Compares every PNG in baselineDir with the file of the same name in otherDir.
export function compareFolders(baselineDir, otherDir, diffDir) {
  const names = fs.readdirSync(baselineDir).filter((f) => f.endsWith(".png")).sort();
  if (names.length === 0) throw new Error(`No PNG screenshots in ${baselineDir}`);
  if (diffDir) fs.mkdirSync(diffDir, { recursive: true });
  const pages = names.map((name) => {
    const other = path.join(otherDir, name);
    if (!fs.existsSync(other)) return { page: name, missing: true };
    const result = comparePngs(readPng(path.join(baselineDir, name)), readPng(other), diffDir && path.join(diffDir, name));
    return { page: name, ...result };
  });
  const compared = pages.filter((p) => !p.missing);
  const percents = compared.map((p) => p.percent);
  return {
    baseline: baselineDir,
    other: otherDir,
    threshold: THRESHOLD,
    pages,
    missing: pages.filter((p) => p.missing).map((p) => p.page),
    max_percent: percents.length ? Math.max(...percents) : null,
    mean_percent: percents.length ? percents.reduce((s, x) => s + x, 0) / percents.length : null,
  };
}

function main() {
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      "diff-dir": { type: "string" },
      limit: { type: "string" },
      json: { type: "string" },
    },
  });
  if (positionals.length !== 2) {
    console.error("Usage: node measurement/pixel_diff.mjs <baseline-dir> <other-dir> [--diff-dir <dir>] [--limit <percent>] [--json <file>]");
    process.exit(2);
  }
  const report = compareFolders(positionals[0], positionals[1], values["diff-dir"]);
  for (const p of report.pages) {
    if (p.missing) {
      console.log(`${p.page.padEnd(22)} missing in ${positionals[1]}`);
      continue;
    }
    const size = p.height[0] === p.height[1] && p.width[0] === p.width[1] ? "" : `  (size ${p.width[0]}x${p.height[0]} vs ${p.width[1]}x${p.height[1]})`;
    console.log(`${p.page.padEnd(22)} ${String(p.mismatched).padStart(8)} of ${String(p.total).padStart(8)} pixels = ${p.percent.toFixed(3)}%${size}`);
  }
  console.log(`max ${report.max_percent.toFixed(3)}%, mean ${report.mean_percent.toFixed(3)}% over ${report.pages.length - report.missing.length} pages`);
  if (values.json) fs.writeFileSync(values.json, JSON.stringify(report, null, 2) + "\n");

  let failed = report.missing.length > 0;
  if (values.limit !== undefined) {
    const limit = Number(values.limit);
    const over = report.pages.filter((p) => !p.missing && p.percent > limit);
    console.log(over.length ? `OVER the ${limit}% limit: ${over.map((p) => p.page).join(", ")}` : `all pages within the ${limit}% limit`);
    failed = failed || over.length > 0;
  }
  process.exit(failed ? 1 : 0);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) main();
