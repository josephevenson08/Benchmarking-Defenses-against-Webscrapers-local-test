// Checks for the generator and server. Run with: npm test
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

const { loadData, buildPages, writeCondition, availableConditions, pageSeed, makeRng, checkDefense } = require("../generate");
const { createApp, listenLocal, runIdFrom } = require("../server");

const data = loadData();
const pages = buildPages(data);

function decode(text) {
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

const ROW = /<div class="field"><span class="label">(.*?)<\/span><span class="value">(.*?)<\/span><\/div>/g;

function rows(html) {
  return [...html.matchAll(ROW)].map((m) => ({ label: decode(m[1]), value: decode(m[2]) }));
}

function itemFor(page) {
  return page.type === "product"
    ? { record: data.items.products.find((p) => p.product_id === page.item_id), fields: data.fields.product }
    : { record: data.items.articles.find((a) => a.article_id === page.item_id), fields: data.fields.article };
}

test("baseline has 10 pages: home, category, 6 products, 2 articles", () => {
  const count = (type) => pages.filter((p) => p.type === type).length;
  assert.equal(pages.length, 10);
  assert.deepEqual([count("home"), count("category"), count("product"), count("article")], [1, 1, 6, 2]);
});

test("every page is reachable by links from the home page", () => {
  const byPath = new Map(pages.map((p) => [p.path, p]));
  const seen = new Set(["/"]);
  const queue = ["/"];
  while (queue.length) {
    const html = byPath.get(queue.shift()).html;
    for (const [, href] of html.matchAll(/href="([^"]+)"/g)) {
      assert.ok(byPath.has(href), `broken link ${href}`);
      if (!seen.has(href)) seen.add(href), queue.push(href);
    }
  }
  assert.deepEqual([...seen].sort(), [...byPath.keys()].sort());
});

test("item pages hold 70 label/value rows matching the data list, in field order", () => {
  let total = 0;
  for (const page of pages.filter((p) => p.item_id)) {
    const { record, fields } = itemFor(page);
    const expected = fields.map((f) => ({ label: f.label, value: record[f.key] }));
    assert.deepEqual(rows(page.html), expected, page.path);
    total += expected.length;
  }
  assert.equal(total, 70);
});

test("no scored value appears anywhere except its own row", () => {
  const values = [
    ...data.items.products.flatMap((p) => data.fields.product.map((f) => p[f.key])),
    ...data.items.articles.flatMap((a) => data.fields.article.map((f) => a[f.key])),
  ];
  for (const page of pages) {
    const text = decode(
      page.html
        .replace(/<style>[\s\S]*?<\/style>/, "")
        .replace(ROW, "")
        .replace(/<[^>]+>/g, " ")
    );
    for (const value of values) assert.ok(!text.includes(value), `"${value}" leaks on ${page.path}`);
  }
});

test("generating twice gives byte-identical files", () => {
  const dirs = [1, 2].map((i) => fs.mkdtempSync(path.join(os.tmpdir(), `site-${i}-`)));
  for (const dir of dirs) writeCondition("baseline", dir);
  for (const page of pages) {
    const [a, b] = dirs.map((dir) => fs.readFileSync(path.join(dir, "baseline", page.file)));
    assert.ok(a.equals(b), page.file);
  }
});

test("the baseline does not depend on the seed", () => {
  const other = buildPages(data, { seed: 1 });
  pages.forEach((page, i) => assert.equal(other[i].html, page.html, page.path));
});

test("every page gets its own seed from the config seed, the condition and the path", () => {
  const seeds = pages.map((p) => p.seed);
  assert.ok(seeds.every((s) => Number.isInteger(s) && s >= 0 && s < 2 ** 32));
  assert.equal(new Set(seeds).size, seeds.length, "seeds differ by page");
  assert.equal(pageSeed(1, "shuffled", "/"), pageSeed(1, "shuffled", "/"));
  assert.notEqual(pageSeed(1, "shuffled", "/"), pageSeed(2, "shuffled", "/"));
  assert.notEqual(pageSeed(1, "shuffled", "/"), pageSeed(1, "honeypot", "/"));
});

test("seeded random numbers repeat for the same seed and stay in [0, 1)", () => {
  const draw = (seed) => Array.from({ length: 1000 }, makeRng(seed));
  assert.deepEqual(draw(42), draw(42));
  assert.notDeepEqual(draw(42), draw(43));
  assert.ok(draw(42).every((x) => x >= 0 && x < 1));
});

test("a defense in the slot gets escaped rows, a seeded random function and its CSS", () => {
  const tricky = JSON.parse(JSON.stringify(data));
  tricky.items.products[0].name = "A & B <C>";
  const build = () => {
    const calls = [];
    const defense = {
      style: ".test-defense { color: red; }",
      fieldRows(rows, rng) {
        calls.push({ rows, draws: [rng(), rng()] });
        return `    <div class="fields test-defense">${rows.length} rows</div>`;
      },
    };
    return { built: buildPages(tricky, { condition: "test", defense, seed: 7 }), calls };
  };
  const first = build();
  const second = build();

  const itemPages = first.built.filter((p) => p.item_id);
  assert.equal(first.calls.length, itemPages.length, "called once per item page");
  first.calls.forEach((call, i) => {
    const { fields } = itemFor(itemPages[i]);
    assert.deepEqual(call.rows.map((r) => r.key), fields.map((f) => f.key), "rows in field order");
    assert.ok(itemPages[i].html.includes(`<div class="fields test-defense">${fields.length} rows</div>`));
  });
  assert.equal(first.calls[0].rows[0].value, "A &amp; B &lt;C&gt;", "values arrive HTML-escaped");
  assert.deepEqual(first.calls.map((c) => c.draws), second.calls.map((c) => c.draws), "same seed, same draws");
  assert.equal(new Set(first.calls.map((c) => c.draws[0])).size, first.calls.length, "each page has its own draws");
  for (const page of first.built) assert.ok(page.html.includes(".test-defense { color: red; }"), page.path);
});

test("a defense file that exports nothing, or returns no HTML, is refused with a clear message", () => {
  assert.throws(() => checkDefense({}, "site/defenses/x.js"), /exports nothing.*module\.exports/);
  assert.throws(() => checkDefense({ fieldRows: "no" }, "site/defenses/x.js"), /must be a function/);
  assert.throws(() => checkDefense({ style: 3 }, "site/defenses/x.js"), /must be a string of CSS/);
  assert.equal(checkDefense({ style: "" }, "x").style, "");
  const silent = { fieldRows() {} };
  assert.throws(() => buildPages(data, { condition: "test", defense: silent, seed: 1 }), /returned nothing/);
});

test("defense files are found by name, and unknown conditions are refused", () => {
  assert.equal(availableConditions()[0], "baseline");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "unknown-"));
  assert.throws(() => writeCondition("no-such-defense", dir), /Unknown or not-yet-built condition "no-such-defense"/);
});

test("the manifest saves the config seed and every page's seed", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "manifest-"));
  writeCondition("baseline", dir, 123);
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, "baseline.manifest.json"), "utf8"));
  assert.equal(manifest.seed, 123);
  assert.equal(manifest.pages.length, 10);
  for (const p of manifest.pages) assert.equal(p.seed, pageSeed(123, "baseline", p.path), p.path);
});

test("run IDs are read from the User-Agent", () => {
  assert.equal(runIdFrom("bench-scraper (run=a-baseline-1)"), "a-baseline-1");
  assert.equal(runIdFrom("Mozilla/5.0 run=b-shuffled-3"), "b-shuffled-3");
  assert.equal(runIdFrom("Mozilla/5.0"), "unknown");
  assert.equal(runIdFrom(undefined), "unknown");
});

test("server serves pages and logs every request", async (t) => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "serve-"));
  const { siteDir } = writeCondition("baseline", outDir);
  const logFile = path.join(outDir, "logs", "requests.jsonl");
  const server = createApp({ siteDir, logFile, trapPath: "/trap" }).listen(0, "127.0.0.1");
  await new Promise((resolve) => server.once("listening", resolve));
  t.after(() => server.close());
  const port = server.address().port;

  // http.get sends no User-Agent unless one is given.
  const get = (urlPath, headers = {}) =>
    new Promise((resolve, reject) => {
      http
        .get({ host: "127.0.0.1", port, path: urlPath, headers }, (res) => {
          let body = "";
          res.on("data", (chunk) => (body += chunk));
          res.on("end", () => resolve({ status: res.statusCode, body }));
        })
        .on("error", reject);
    });
  const ua = (run) => ({ "User-Agent": `bench-scraper (run=${run})` });

  const product = await get("/products/p1", ua("a-baseline-1"));
  assert.equal(product.status, 200);
  assert.match(product.body, /Larkfield Studio Headphones/);
  assert.equal((await get("/products/", ua("a-baseline-1"))).status, 200);
  assert.equal((await get("/robots.txt", ua("a-baseline-1"))).body, "User-agent: *\nDisallow:\n");
  assert.equal((await get("/trap", ua("a-baseline-2"))).status, 200);
  assert.equal((await get("/missing", ua("a-baseline-2"))).status, 404);
  assert.equal((await get("/")).status, 200);

  // Log lines are written when each response finishes, so wait for all six.
  let lines = [];
  for (let i = 0; i < 50 && lines.length < 6; i++) {
    await new Promise((resolve) => setTimeout(resolve, 20));
    lines = fs.existsSync(logFile) ? fs.readFileSync(logFile, "utf8").trim().split("\n").map(JSON.parse) : [];
  }
  assert.equal(lines.length, 6);
  const pick = (e) => [e.run_id, e.path, e.status, e.honeypot_hit];
  assert.deepEqual(lines.map(pick), [
    ["a-baseline-1", "/products/p1", 200, false],
    ["a-baseline-1", "/products/", 200, false],
    ["a-baseline-1", "/robots.txt", 200, false],
    ["a-baseline-2", "/trap", 200, true],
    ["a-baseline-2", "/missing", 404, false],
    ["unknown", "/", 200, false],
  ]);
  for (const e of lines) {
    assert.equal(typeof e.response_ms, "number");
    assert.ok(!Number.isNaN(Date.parse(e.timestamp)));
  }
  assert.equal(lines[5].user_agent, null);
});

test("server listens on the IPv4 loopback, and on IPv6 where available", async (t) => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "listen-"));
  const { siteDir } = writeCondition("baseline", outDir);
  const app = createApp({ siteDir, logFile: path.join(outDir, "requests.jsonl"), trapPath: "/trap" });

  // Find a free port, then listen on it from both loopback addresses.
  const probe = http.createServer().listen(0, "127.0.0.1");
  await new Promise((resolve) => probe.once("listening", resolve));
  const port = probe.address().port;
  await new Promise((resolve) => probe.close(resolve));

  const listening = [];
  const servers = listenLocal(app, port, (host) => listening.push(host));
  t.after(() => servers.filter((s) => s.listening).forEach((s) => s.close()));
  for (let i = 0; i < 50 && !listening.includes("127.0.0.1"); i++) {
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  await new Promise((resolve) => setTimeout(resolve, 50));

  const status = (host) =>
    new Promise((resolve, reject) => {
      http.get({ host, port, path: "/" }, (res) => (res.resume(), resolve(res.statusCode))).on("error", reject);
    });
  assert.ok(listening.includes("127.0.0.1"));
  assert.equal(await status("127.0.0.1"), 200);
  if (listening.includes("::1")) assert.equal(await status("::1"), 200);
});
