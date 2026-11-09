// Checks for measurement/pixel_diff.mjs. Run with: npm test
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import pngjs from "pngjs";
import { comparePngs, compareFolders } from "./pixel_diff.mjs";

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
