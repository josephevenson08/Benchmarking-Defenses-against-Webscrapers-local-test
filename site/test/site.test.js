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

test("a defense's mainEnd adds HTML at the end of every page's main and gets the trap path", () => {
  const seen = [];
  const defense = {
    mainEnd(page, rng) {
      seen.push({ ...page, draw: rng() });
      return `    <a class="test-trap" href="${page.trapPath}">trap</a>`;
    },
  };
  const built = buildPages(data, { condition: "test", defense, seed: 3 });
  assert.deepEqual(seen.map((p) => p.path), built.map((p) => p.path), "called once per page, all 10");
  assert.ok(seen.every((p) => p.trapPath === "/trap"), "trap path from config.json");
  assert.equal(seen.find((p) => p.path === "/products/p1").item_id, "p1");
  assert.equal(seen.find((p) => p.path === "/").type, "home");
  for (const page of built) {
    assert.match(page.html, /<a class="test-trap" href="\/trap">trap<\/a>\n  <\/main>/, page.path);
  }
  for (const page of built.filter((p) => p.item_id)) {
    const { record, fields } = itemFor(page);
    assert.deepEqual(rows(page.html), fields.map((f) => ({ label: f.label, value: record[f.key] })), "fields untouched");
  }
  assert.throws(() => buildPages(data, { condition: "test", defense: { mainEnd() {} }, seed: 1 }), /mainEnd must return/);
  assert.throws(() => checkDefense({ mainEnd: 3 }, "x"), /"mainEnd" must be a function/);
});

test("poisoning: fakes in the HTML, real values in values/, every fake in the fakes file", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "poison-"));
  // A stand-in defense that only exercises the slot: not the project's fakes or swap script.
  const defense = {
    fakeValue: (row, rng) => `Fake ${Math.floor(rng() * 1000)} ${row.value}`,
    script: (page) => (page.valuesPath ? `console.log(${JSON.stringify(page.valuesPath)});` : ""),
  };
  const first = writeCondition("test-poison", dir, 11, defense);
  const read = (file) => fs.readFileSync(path.join(dir, file), "utf8");
  const fakes = JSON.parse(read("test-poison.fakes.json"));
  assert.equal(fakes.length, 70, "one fake per scored field");
  assert.ok(!fs.existsSync(path.join(first.siteDir, "test-poison.fakes.json")), "fakes file is not served");

  for (const page of first.pages.filter((p) => p.item_id)) {
    const { record, fields } = itemFor(page);
    const html = read(path.join("test-poison", page.file));
    const shown = rows(html);
    const mine = fakes.filter((f) => f.item_id === page.item_id);
    assert.deepEqual(shown.map((r) => r.label), fields.map((f) => f.label), "labels unchanged");
    assert.deepEqual(shown.map((r) => r.value), mine.map((f) => f.fake_value), "rows show the fakes");
    assert.deepEqual(mine.map((f) => f.field), fields.map((f) => f.key), "fakes file in field order");
    for (const f of fields) assert.ok(!shown.some((r) => r.value === record[f.key]), `${page.item_id} ${f.key} hidden`);

    assert.equal(page.valuesPath, `/values${page.path}.json`);
    const values = JSON.parse(read(path.join("test-poison", page.valuesPath)));
    assert.equal(values.item_id, page.item_id);
    assert.deepEqual(values.fields, fields.map((f) => ({ key: f.key, label: f.label, value: record[f.key] })), "real values");
    assert.ok(html.endsWith(`  <script>\nconsole.log("${page.valuesPath}");\n  </script>\n</body>\n</html>\n`), page.path);
  }
  for (const page of first.pages.filter((p) => !p.item_id)) {
    assert.ok(!read(path.join("test-poison", page.file)).includes("<script>"), `no script on ${page.path}`);
  }
  const manifest = JSON.parse(read("test-poison.manifest.json"));
  assert.equal(manifest.fakes_file, "test-poison.fakes.json");
  assert.equal(manifest.pages.find((p) => p.path === "/products/p1").values, "/values/products/p1.json");

  writeCondition("test-poison", dir, 11, defense);
  assert.deepEqual(JSON.parse(read("test-poison.fakes.json")), fakes, "same seed, same fakes");
  writeCondition("test-poison", dir, 12, defense);
  assert.notDeepEqual(JSON.parse(read("test-poison.fakes.json")), fakes, "another seed, other fakes");
});

test("poisoning refuses a fake that equals the real value, an empty fake, and script tags", () => {
  const build = (defense) => buildPages(data, { condition: "test", defense, seed: 1 });
  assert.throws(() => build({ fakeValue: (row) => ` ${row.value.toUpperCase()} ` }), /fakeValue for p1 name returned the real value/);
  assert.throws(() => build({ fakeValue: () => "  " }), /must return the fake as non-empty text/);
  assert.throws(() => build({ fakeValue: () => undefined }), /returned nothing/);
  assert.throws(() => build({ script: () => "<script>x()</script>" }), /without <script> tags/);
  assert.throws(() => build({ script: () => 3 }), /script must return JavaScript/);
  assert.throws(() => checkDefense({ fakeValue: "x" }, "x"), /"fakeValue" must be a function \(row, rng\)/);
  const plain = build({ style: "" });
  assert.ok(plain.every((p) => !p.fakes && !p.valuesPath), "no poisoning without fakeValue");
});

test("tarpit hooks: footer adds HTML to every page's footer, disallow goes into robots.txt", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "tarpit-"));
  const seen = [];
  const defense = {
    footer(page, rng) {
      seen.push({ path: page.path, draw: rng() });
      return `<a class="test-entrance" href="/maze/test">more</a>`;
    },
    disallow: ["/maze/"],
  };
  const { pages, siteDir } = writeCondition("test-tarpit", dir, 5, defense);
  assert.deepEqual(seen.map((s) => s.path), pages.map((p) => p.path), "called once per page, all 10");
  for (const page of pages) {
    assert.match(page.html, /All content is made up\. <a class="test-entrance" href="\/maze\/test">more<\/a><\/footer>/, page.path);
  }
  assert.equal(fs.readFileSync(path.join(siteDir, "robots.txt"), "utf8"), "User-agent: *\nDisallow: /maze/\n");
  assert.ok(!fs.existsSync(path.join(dir, "test-tarpit.fakes.json")), "no fakes file without poisoning");
  assert.throws(() => checkDefense({ disallow: "/maze/" }, "x"), /"disallow" must be a list of paths/);
  assert.throws(() => checkDefense({ disallow: ["maze"] }, "x"), /"disallow" must be a list of paths/);
  assert.throws(() => checkDefense({ maze: {} }, "x"), /"maze" must be a function \(req, res\)/);
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

test("server answers /maze/<hash> with the defense's route, adds its log fields, and serves real values", async (t) => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "maze-"));
  const { siteDir } = writeCondition("test-poison", outDir, 3, { fakeValue: (row) => `Fake ${row.value}` });
  const logFile = path.join(outDir, "logs", "requests.jsonl");
  // A stand-in route that only exercises the slot: not the project's tarpit.
  const defense = {
    maze(req, res) {
      res.locals.log = { maze_hash: req.params.hash, run_id: "not-allowed", path: "/nope" };
      res.type("html").send(`<p>${req.params.hash}</p>`);
    },
  };
  const servers = [
    createApp({ siteDir, logFile, trapPath: "/trap", defense }).listen(0, "127.0.0.1"),
    createApp({ siteDir, logFile: path.join(outDir, "logs", "plain.jsonl"), trapPath: "/trap" }).listen(0, "127.0.0.1"),
  ];
  await Promise.all(servers.map((s) => new Promise((resolve) => s.once("listening", resolve))));
  t.after(() => servers.forEach((s) => s.close()));
  const get = (server, urlPath) =>
    new Promise((resolve, reject) => {
      const headers = { "User-Agent": "bench-scraper (run=a-tarpit-1)" };
      http
        .get({ host: "127.0.0.1", port: server.address().port, path: urlPath, headers }, (res) => {
          let body = "";
          res.on("data", (chunk) => (body += chunk));
          res.on("end", () => resolve({ status: res.statusCode, body, type: res.headers["content-type"] }));
        })
        .on("error", reject);
    });

  const maze = await get(servers[0], "/maze/abc123");
  assert.equal(maze.status, 200);
  assert.equal(maze.body, "<p>abc123</p>");
  assert.equal((await get(servers[1], "/maze/abc123")).status, 404, "no maze route without the export");
  const values = await get(servers[0], "/values/products/p1.json");
  assert.equal(values.status, 200);
  assert.match(values.type, /application\/json/);
  assert.equal(JSON.parse(values.body).fields[0].value, "Larkfield Studio Headphones");

  let lines = [];
  for (let i = 0; i < 50 && lines.length < 2; i++) {
    await new Promise((resolve) => setTimeout(resolve, 20));
    lines = fs.existsSync(logFile) ? fs.readFileSync(logFile, "utf8").trim().split("\n").map(JSON.parse) : [];
  }
  assert.equal(lines.length, 2);
  assert.deepEqual([lines[0].run_id, lines[0].path, lines[0].maze_hash], ["a-tarpit-1", "/maze/abc123", "abc123"], "extra field added, standard ones kept");
  assert.equal(lines[0].user_agent, "bench-scraper (run=a-tarpit-1)");
  assert.equal(lines[1].maze_hash, undefined);
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
