// Checks for measurement/pixel_diff.mjs. Run with: npm test
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import pngjs from "pngjs";
import { comparePngs, compareFolders, ssim } from "./pixel_diff.mjs";

const { PNG } = pngjs;

function image(width, height, rgb = [255, 255, 255]) {
  const png = new PNG({ width, height });
  for (let i = 0; i < width * height; i++) png.data.set([...rgb, 255], i * 4);
  return png;
}

function paint(png, x, y, rgb) {
  png.data.set([...rgb, 255], (y * png.width + x) * 4);
  return png;
}

test("identical images differ in 0 pixels", () => {
  const r = comparePngs(image(20, 10), image(20, 10));
  assert.equal(r.mismatched, 0);
  assert.equal(r.total, 200);
  assert.equal(r.percent, 0);
});

test("one changed pixel counts as 1 of the total", () => {
  const r = comparePngs(image(20, 10), paint(image(20, 10), 3, 4, [0, 0, 0]));
  assert.equal(r.mismatched, 1);
  assert.equal(r.percent, 0.5);
});

test("pixels that exist in only one image count as different", () => {
  const r = comparePngs(image(20, 10), image(20, 12));
  assert.equal(r.total, 240);
  assert.equal(r.mismatched, 40);
  assert.deepEqual(r.height, [10, 12]);
});

test("folders are compared page by page, and missing pages are reported", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pixel-"));
  const [a, b, diff] = ["a", "b", "diff"].map((d) => path.join(dir, d));
  fs.mkdirSync(a);
  fs.mkdirSync(b);
  const write = (folder, name, png) => fs.writeFileSync(path.join(folder, name), PNG.sync.write(png));
  write(a, "index.png", image(10, 10));
  write(b, "index.png", image(10, 10));
  write(a, "products-p1.png", image(10, 10));
  write(b, "products-p1.png", paint(paint(image(10, 10), 0, 0, [0, 0, 0]), 9, 9, [0, 0, 0]));
  write(a, "articles-a1.png", image(10, 10));

  const report = compareFolders(a, b, diff);
  assert.deepEqual(report.pages.map((p) => p.page), ["articles-a1.png", "index.png", "products-p1.png"]);
  assert.deepEqual(report.missing, ["articles-a1.png"]);
  assert.equal(report.pages.find((p) => p.page === "products-p1.png").mismatched, 2);
  assert.equal(report.max_percent, 2);
  assert.equal(report.mean_percent, 1);
  assert.ok(fs.existsSync(path.join(diff, "products-p1.png")), "diff image written");
});

// A 40x40 grey image with a deterministic pattern, so SSIM has structure to compare.
function pattern(seed = 1, size = 40) {
  const png = new PNG({ width: size, height: size });
  let state = seed;
  for (let i = 0; i < size * size; i++) {
    state = (state * 1103515245 + 12345) % 2147483648;
    const v = 60 + (state % 140);
    png.data.set([v, v, v, 255], i * 4);
  }
  return png;
}

test("SSIM is 1 for identical images and symmetric", () => {
  assert.equal(ssim(pattern(), pattern()), 1);
  const a = pattern(1);
  const b = pattern(2);
  assert.ok(Math.abs(ssim(a, b) - ssim(b, a)) < 1e-12);
});

test("SSIM drops as the image changes more", () => {
  const a = pattern(1);
  const slightly = pattern(1);
  for (let x = 0; x < 40; x += 7) paint(slightly, x, 20, [0, 0, 0]);
  const unrelated = pattern(7);
  const small = ssim(a, slightly);
  const large = ssim(a, unrelated);
  assert.ok(small < 1 && small > 0.8, `small change gave ${small}`);
  assert.ok(large < small, `unrelated image gave ${large}`);
});

test("SSIM needs at least one 11x11 window and is reported per page", () => {
  assert.equal(ssim(image(10, 10), image(10, 10)), null);
  const r = comparePngs(pattern(1), pattern(1));
  assert.equal(r.ssim, 1);
});

