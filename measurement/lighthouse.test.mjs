// Checks for measurement/lighthouse.mjs that need no browser. Run with: npm test
import test from "node:test";
import assert from "node:assert/strict";
import { median, medians, measuresOf } from "./lighthouse.mjs";

test("median of an odd and an even number of runs, ignoring missing values", () => {
  assert.equal(median([5, 1, 3]), 3);
  assert.equal(median([4, 1, 3, 2]), 2.5);
  assert.equal(median([null, 7, undefined]), 7);
  assert.equal(median([]), null);
});

test("measures are read from a Lighthouse result and the score becomes 0-100", () => {
  const lhr = {
    categories: { performance: { score: 0.97 } },
    audits: {
      "first-contentful-paint": { numericValue: 600 },
      "largest-contentful-paint": { numericValue: 700 },
      interactive: { numericValue: 800 },
      "total-blocking-time": { numericValue: 0 },
      "cumulative-layout-shift": { numericValue: 0.01 },
    },
  };
  assert.deepEqual(measuresOf(lhr), { score: 97, fcp_ms: 600, lcp_ms: 700, tti_ms: 800, tbt_ms: 0, cls: 0.01 });
  assert.equal(measuresOf({ categories: { performance: { score: 1 } }, audits: {} }).tti_ms, null);
});

test("each measure gets its own median over the runs", () => {
  const runs = [
    { score: 100, fcp_ms: 600, lcp_ms: 600, tti_ms: 600, tbt_ms: 0, cls: 0 },
    { score: 98, fcp_ms: 900, lcp_ms: 650, tti_ms: 700, tbt_ms: 10, cls: 0 },
    { score: 99, fcp_ms: 610, lcp_ms: 640, tti_ms: 650, tbt_ms: 0, cls: 0 },
  ];
  assert.deepEqual(medians(runs), { score: 99, fcp_ms: 610, lcp_ms: 640, tti_ms: 650, tbt_ms: 0, cls: 0 });
});
