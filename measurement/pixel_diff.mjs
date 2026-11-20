// Compares two folders of page screenshots with pixelmatch and reports, for each
// page, the share of pixels that differ (midterm §2 Measurement, §3: "a short Node
// script reads two PNGs and counts mismatched pixels, which I divide by the
// page's total pixels"). Used for Test 4 (shuffled vs baseline, at most 1%).
//
// It also reports SSIM, the structural similarity index of Wang, Bovik, Sheikh and
// Simoncelli (IEEE TIP 2004), D70: 1.0 means identical. Computed on the luminance
// (Rec. 601 weights) at full resolution with the paper's 11x11 Gaussian window
// (sigma 1.5) and constants K1 = 0.01, K2 = 0.03, L = 255, averaged over every
// window that fits inside the image. When the two screenshots differ in size, SSIM
// covers the part they share and the size difference shows in the pixel count.
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

// Luminance of the top-left width x height part of an image, as floats.
function luminance(png, width, height) {
  const out = new Float64Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * png.width + x) * 4;
      out[y * width + x] = 0.299 * png.data[i] + 0.587 * png.data[i + 1] + 0.114 * png.data[i + 2];
    }
  }
  return out;
}

const SSIM_RADIUS = 5; // 11x11 window
const SSIM_SIGMA = 1.5;
const SSIM_C1 = (0.01 * 255) ** 2;
const SSIM_C2 = (0.03 * 255) ** 2;

function gaussianKernel() {
  const k = [];
  for (let i = -SSIM_RADIUS; i <= SSIM_RADIUS; i++) k.push(Math.exp(-(i * i) / (2 * SSIM_SIGMA * SSIM_SIGMA)));
  const sum = k.reduce((s, v) => s + v, 0);
  return k.map((v) => v / sum);
}

// Gaussian-weighted local mean of img over every window that fits ("valid" region).
function blurValid(img, width, height, kernel) {
  const n = kernel.length;
  const w = width - n + 1;
  const h = height - n + 1;
  const rows = new Float64Array(w * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < w; x++) {
      let s = 0;
      for (let k = 0; k < n; k++) s += kernel[k] * img[y * width + x + k];
      rows[y * w + x] = s;
    }
  }
  const out = new Float64Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let s = 0;
      for (let k = 0; k < n; k++) s += kernel[k] * rows[(y + k) * w + x];
      out[y * w + x] = s;
    }
  }
  return out;
}

// Mean SSIM of two decoded PNGs over the part they share; null if that part is smaller than one window.
export function ssim(a, b) {
  const width = Math.min(a.width, b.width);
  const height = Math.min(a.height, b.height);
  const kernel = gaussianKernel();
  if (width < kernel.length || height < kernel.length) return null;
  const x = luminance(a, width, height);
  const y = luminance(b, width, height);
  const xx = x.map((v) => v * v);
  const yy = y.map((v) => v * v);
  const xy = x.map((v, i) => v * y[i]);
  const [mx, my, sxx, syy, sxy] = [x, y, xx, yy, xy].map((img) => blurValid(img, width, height, kernel));
  let total = 0;
  for (let i = 0; i < mx.length; i++) {
    const vx = sxx[i] - mx[i] * mx[i];
    const vy = syy[i] - my[i] * my[i];
    const cov = sxy[i] - mx[i] * my[i];
    total += ((2 * mx[i] * my[i] + SSIM_C1) * (2 * cov + SSIM_C2)) /
      ((mx[i] * mx[i] + my[i] * my[i] + SSIM_C1) * (vx + vy + SSIM_C2));
  }
  return total / mx.length;
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
    ssim: ssim(a, b),
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
  const ssims = compared.map((p) => p.ssim).filter((v) => v !== null);
  return {
    baseline: baselineDir,
    other: otherDir,
    threshold: THRESHOLD,
    pages,
    missing: pages.filter((p) => p.missing).map((p) => p.page),
    max_percent: percents.length ? Math.max(...percents) : null,
    mean_percent: percents.length ? percents.reduce((s, x) => s + x, 0) / percents.length : null,
    min_ssim: ssims.length ? Math.min(...ssims) : null,
    mean_ssim: ssims.length ? ssims.reduce((s, x) => s + x, 0) / ssims.length : null,
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
    const s = p.ssim === null ? "n/a" : p.ssim.toFixed(4);
    console.log(`${p.page.padEnd(22)} ${String(p.mismatched).padStart(8)} of ${String(p.total).padStart(8)} pixels = ${p.percent.toFixed(3)}%  SSIM ${s}${size}`);
  }
  console.log(`max ${report.max_percent.toFixed(3)}%, mean ${report.mean_percent.toFixed(3)}% over ${report.pages.length - report.missing.length} pages`);
  if (report.mean_ssim !== null) console.log(`SSIM mean ${report.mean_ssim.toFixed(4)}, min ${report.min_ssim.toFixed(4)}`);
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
