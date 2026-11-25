// Builds one condition of the test site from the data list.
//
//   node site/generate.js baseline
//   node site/generate.js shuffled      (once site/defenses/shuffled.js exists)
//
// Writes the 10 pages and robots.txt to conditions/<condition>/, and a manifest
// of the pages to conditions/<condition>.manifest.json. The manifest sits
// outside the served folder so scrapers can't fetch it.
//
// A poisoning defense (one that exports fakeValue) also gets each item page's
// real values as JSON in conditions/<condition>/values/ (served, so the page's
// script can fetch them) and every fake in conditions/<condition>.fakes.json
// (not served: it is for scoring, midterm §2 and Figure 2's FakeValue).
//
// Defenses plug in as one file per condition in site/defenses/ (see the README
// there). Every page gets its own seed, made from the seed in config.json, the
// condition and the page path, and the manifest saves them (midterm §5). The same
// config seed therefore rebuilds every condition byte for byte.
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const SITE_NAME = "Demo Shop";
const DEFENSES_DIR = path.join(__dirname, "defenses");

// The conditions that can be built: baseline, plus one per defense file.
function availableConditions() {
  const defenses = fs.existsSync(DEFENSES_DIR)
    ? fs
        .readdirSync(DEFENSES_DIR)
        .filter((f) => f.endsWith(".js"))
        .map((f) => f.slice(0, -3))
        .sort()
    : [];
  return ["baseline", ...defenses];
}

function loadConfig() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, "config.json"), "utf8"));
}

// Seed for one page: a 32-bit FNV-1a hash of "<config seed>:<condition>:<path>".
function pageSeed(baseSeed, condition, pagePath) {
  let hash = 0x811c9dc5;
  for (const ch of `${baseSeed}:${condition}:${pagePath}`) {
    hash ^= ch.codePointAt(0);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash;
}

// Seeded random numbers (mulberry32). makeRng(seed) returns a function that gives
// a number in [0, 1) on each call, the same sequence every time for the same seed.
function makeRng(seed) {
  let state = seed >>> 0;
  return function rng() {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// A defense file exports any of these hooks (see site/defenses/README.md):
//   style      extra CSS (text) added to every page's <style>
//   fieldRows  function (rows, rng) returning the HTML of an item page's fields block
//   mainEnd    function (page, rng) returning HTML added at the end of every page's <main>
//   fakeValue  function (row, rng) returning the fake shown in the HTML for one field (poisoning)
//   script     function (page) returning JavaScript run on the page, in a <script> at the end of <body>
//   footer     function (page, rng) returning HTML added at the end of every page's <footer>
//   disallow   list of paths that robots.txt disallows, e.g. ["/maze/"]
//   maze       function (req, res) answering GET /maze/<hash>; used by site/server.js, not here (tarpit)
const HOOKS = {
  style: "a string of CSS",
  fieldRows: "a function (rows, rng)",
  mainEnd: "a function (page, rng)",
  fakeValue: "a function (row, rng)",
  script: "a function (page)",
  footer: "a function (page, rng)",
  disallow: 'a list of paths, like ["/maze/"]',
  maze: "a function (req, res)",
};

function loadDefense(condition) {
  if (condition === "baseline") return null;
  return checkDefense(require(path.join(DEFENSES_DIR, `${condition}.js`)), `site/defenses/${condition}.js`);
}

function checkDefense(defense, name) {
  if (!defense || !Object.keys(HOOKS).some((hook) => defense[hook] !== undefined)) {
    throw new Error(
      `${name} exports nothing the generator can use. Add module.exports = { ... } at the end, with any of: ${Object.keys(HOOKS).join(", ")}.`
    );
  }
  for (const [hook, kind] of Object.entries(HOOKS)) {
    const value = defense[hook];
    if (value === undefined) continue;
    const ok =
      hook === "style"
        ? typeof value === "string"
        : hook === "disallow"
          ? Array.isArray(value) && value.every((p) => typeof p === "string" && p.startsWith("/"))
          : typeof value === "function";
    if (!ok) throw new Error(`${name}: "${hook}" must be ${kind}.`);
  }
  return defense;
}

function loadData() {
  const read = (file) => JSON.parse(fs.readFileSync(path.join(ROOT, "data", file), "utf8"));
  return { items: read("items.json"), fields: read("fields.json") };
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const STYLE = `
    body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.5; color: #1f2328; background: #fff; }
    header, main, footer { max-width: 44rem; margin: 0 auto; padding: 1rem; }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #d0d7de; }
    .brand { font-weight: 700; color: inherit; text-decoration: none; }
    nav a { margin-left: 1rem; }
    a { color: #0969da; }
    .fields { display: flex; flex-direction: column; }
    .field { display: flex; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid #eaeef2; }
    .label { flex: 0 0 9rem; font-weight: 600; }
    .value { flex: 1; }
    footer { color: #57606a; font-size: 0.875rem; border-top: 1px solid #d0d7de; }`;

// extra: { style, footer, script } from a defense; each is "" when there is none.
function layout(title, main, extra = {}) {
  const { style: extraStyle = "", footer = "", script = "" } = extra;
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} · ${SITE_NAME}</title>
  <style>${STYLE}${extraStyle ? "\n" + extraStyle : ""}
  </style>
</head>
<body>
  <header>
    <a class="brand" href="/">${SITE_NAME}</a>
    <nav><a href="/">Home</a><a href="/products/">Products</a></nav>
  </header>
  <main>
${main}
  </main>
  <footer>Synthetic test site for a local scraping study. All content is made up.${footer ? " " + footer : ""}</footer>
${script ? `  <script>\n${script}\n  </script>\n` : ""}</body>
</html>
`;
}

// One flex row per field: a label element, then a value element.
function fieldRows(item, fieldList) {
  const rows = fieldList.map(
    (f) =>
      `      <div class="field"><span class="label">${escapeHtml(f.label)}</span>` +
      `<span class="value">${escapeHtml(item[f.key])}</span></div>`
  );
  return `    <div class="fields">\n${rows.join("\n")}\n    </div>`;
}

// The fields block of an item page: the baseline rows, or the defense's version.
// The defense gets the rows in field order with label and value already
// HTML-escaped, and the page's seeded random function.
function fieldsBlock(item, fieldList, defense, rng) {
  if (!defense || !defense.fieldRows) return fieldRows(item, fieldList);
  const rows = fieldList.map((f) => ({ key: f.key, label: escapeHtml(f.label), value: escapeHtml(item[f.key]) }));
  const html = defense.fieldRows(rows, rng);
  if (typeof html !== "string") {
    throw new Error(`fieldRows must return the fields block as a string of HTML (it returned ${html === undefined ? "nothing" : typeof html}).`);
  }
  return html;
}

// Extra HTML for the end of a page's <main>: "" without a defense, otherwise what
// the defense's mainEnd returns, on a new line. The defense gets the page's path,
// type, item_id (item pages only) and the trap path from config.json.
function mainEnd(defense, page, rng) {
  if (!defense || !defense.mainEnd) return "";
  const html = defense.mainEnd(page, rng);
  if (typeof html !== "string") {
    throw new Error(`mainEnd must return a string of HTML (it returned ${html === undefined ? "nothing" : typeof html}).`);
  }
  return html ? "\n" + html : "";
}

// HTML for the end of a page's <footer> (for example the tarpit's entrance link).
function footerEnd(defense, page, rng) {
  if (!defense || !defense.footer) return "";
  const html = defense.footer(page, rng);
  if (typeof html !== "string") {
    throw new Error(`footer must return a string of HTML (it returned ${html === undefined ? "nothing" : typeof html}).`);
  }
  return html;
}

// The JavaScript a defense runs on a page (for example poisoning's swap script).
function pageScript(defense, page) {
  if (!defense || !defense.script) return "";
  const js = defense.script(page);
  if (typeof js !== "string") {
    throw new Error(`script must return JavaScript as a string (it returned ${js === undefined ? "nothing" : typeof js}).`);
  }
  if (/<\/script/i.test(js)) {
    throw new Error(`script must return only the JavaScript, without <script> tags: the generator adds them (page ${page.path}).`);
  }
  return js;
}

// Poisoning: the fake for every field of one item page, from the defense's
// fakeValue(row, rng). The row's value is the real value as text (not
// HTML-escaped); the generator escapes the fake when it writes the page.
// Each page has one seeded random function for all its fields, so the same seed
// gives the same fakes (midterm §6: fixed fakes per page).
const same = (a, b) => String(a).trim().replace(/\s+/g, " ").toLowerCase() === String(b).trim().replace(/\s+/g, " ").toLowerCase();

function fakesFor(defense, itemId, item, fieldList, rng) {
  return fieldList.map((f) => {
    const real = String(item[f.key]);
    const fake = defense.fakeValue({ key: f.key, label: f.label, value: real }, rng);
    const where = `fakeValue for ${itemId} ${f.key}`;
    if (typeof fake !== "string" || fake.trim() === "") {
      throw new Error(`${where} must return the fake as non-empty text (it returned ${fake === undefined ? "nothing" : JSON.stringify(fake)}).`);
    }
    if (same(fake, real)) {
      throw new Error(`${where} returned the real value (${JSON.stringify(real)}). A fake must differ from the real value.`);
    }
    return { key: f.key, label: f.label, real, fake };
  });
}

function linkList(links) {
  const items = links.map((l) => `      <li><a href="${l.href}">${escapeHtml(l.text)}</a></li>`);
  return `    <ul>\n${items.join("\n")}\n    </ul>`;
}

// Link text and titles use "Product 1", "Article 1" and so on, never a scored
// value, so each value appears only in its own row on its own page.
//
// options: condition (default "baseline"), defense (a loaded defense file, or
// null for none) and seed (default: the seed in config.json).
function buildPages({ items, fields }, options = {}) {
  const condition = options.condition || "baseline";
  const defense = options.defense || null;
  const baseSeed = options.seed !== undefined ? options.seed : loadConfig().seed;
  const style = (defense && defense.style) || "";
  const seedFor = (pagePath) => pageSeed(baseSeed, condition, pagePath);
  const trapPath = options.trapPath || loadConfig().trap_path;
  const poisoned = Boolean(defense && defense.fakeValue);
  // Each page's HTML. A defense's hooks can add HTML at the end of <main> and of
  // <footer>, and a script at the end of <body>. Each hook gets its own copy of
  // the page's seeded random function, so one hook's draws never shift another's.
  const page = (title, main, info) => {
    const hookPage = { ...info, trapPath };
    return layout(title, main + mainEnd(defense, hookPage, makeRng(seedFor(info.path))), {
      style,
      footer: footerEnd(defense, hookPage, makeRng(seedFor(info.path))),
      script: pageScript(defense, hookPage),
    });
  };
  // An item page's fields block. With poisoning, the rows show the fakes, and the
  // real values and fakes are kept with the page for writeCondition.
  const itemPage = (pagePath, id, item, fieldList) => {
    if (!poisoned) return { fields: fieldsBlock(item, fieldList, defense, makeRng(seedFor(pagePath))), extra: {} };
    const fakes = fakesFor(defense, id, item, fieldList, makeRng(seedFor(pagePath)));
    const shown = { ...item, ...Object.fromEntries(fakes.map((f) => [f.key, f.fake])) };
    return {
      fields: fieldsBlock(shown, fieldList, defense, makeRng(seedFor(pagePath))),
      extra: { valuesPath: `/values${pagePath}.json`, fakes },
    };
  };

  const products = items.products.map((p, i) => ({ item: p, id: p.product_id, n: i + 1 }));
  const articles = items.articles.map((a, i) => ({ item: a, id: a.article_id, n: i + 1 }));

  const pages = [
    {
      path: "/",
      file: "index.html",
      type: "home",
      html: page(
        "Home",
        `    <h1>${SITE_NAME}</h1>
    <p>Browse the product catalog or read the latest articles.</p>
    <h2>Shop</h2>
${linkList([{ href: "/products/", text: "All products" }])}
    <h2>Articles</h2>
${linkList(articles.map((a) => ({ href: `/articles/${a.id}`, text: `Article ${a.n}` })))}`,
        { path: "/", type: "home" }
      ),
    },
    {
      path: "/products/",
      file: "products/index.html",
      type: "category",
      html: page(
        "Products",
        `    <h1>Products</h1>
${linkList(products.map((p) => ({ href: `/products/${p.id}`, text: `Product ${p.n}` })))}`,
        { path: "/products/", type: "category" }
      ),
    },
  ];

  for (const p of products) {
    const pagePath = `/products/${p.id}`;
    const { fields: block, extra } = itemPage(pagePath, p.id, p.item, fields.product);
    const info = { path: pagePath, type: "product", item_id: p.id, ...(extra.valuesPath && { valuesPath: extra.valuesPath }) };
    pages.push({
      path: pagePath,
      file: `products/${p.id}.html`,
      type: "product",
      item_id: p.id,
      html: page(`Product ${p.n}`, `    <h1>Product details</h1>\n${block}`, info),
      ...extra,
    });
  }
  for (const a of articles) {
    const pagePath = `/articles/${a.id}`;
    const { fields: block, extra } = itemPage(pagePath, a.id, a.item, fields.article);
    const info = { path: pagePath, type: "article", item_id: a.id, ...(extra.valuesPath && { valuesPath: extra.valuesPath }) };
    pages.push({
      path: pagePath,
      file: `articles/${a.id}.html`,
      type: "article",
      item_id: a.id,
      html: page(`Article ${a.n}`, `    <h1>Article</h1>\n${block}`, info),
      ...extra,
    });
  }
  for (const pg of pages) pg.seed = seedFor(pg.path);
  return pages;
}

const ROBOTS_TXT = "User-agent: *\nDisallow:\n";

// robots.txt: allows everything, unless the defense lists paths to disallow.
function robotsTxt(defense) {
  const paths = (defense && defense.disallow) || [];
  if (paths.length === 0) return ROBOTS_TXT;
  return "User-agent: *\n" + paths.map((p) => `Disallow: ${p}\n`).join("");
}

// defenseOverride (for tests): a defense object to use instead of site/defenses/<condition>.js.
function writeCondition(condition, outDir = path.join(ROOT, "conditions"), seed = loadConfig().seed, defenseOverride) {
  const available = availableConditions();
  if (!defenseOverride && !available.includes(condition)) {
    throw new Error(`Unknown or not-yet-built condition "${condition}". Built so far: ${available.join(", ")}.`);
  }
  const data = loadData();
  const defense = defenseOverride ? checkDefense(defenseOverride, "test defense") : loadDefense(condition);
  const pages = buildPages(data, { condition, defense, seed });
  const siteDir = path.join(outDir, condition);
  const fakesFile = path.join(outDir, `${condition}.fakes.json`);

  fs.rmSync(siteDir, { recursive: true, force: true });
  fs.rmSync(fakesFile, { force: true });
  const write = (file, text) => {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, text);
  };
  for (const page of pages) write(path.join(siteDir, page.file), page.html);
  fs.writeFileSync(path.join(siteDir, "robots.txt"), robotsTxt(defense));

  // Poisoning: each item page's real values, fetched by the page's script, and
  // every fake as a FakeValue row (midterm Figure 2; D35's format).
  const poisonedPages = pages.filter((p) => p.fakes);
  for (const page of poisonedPages) {
    const values = { item_id: page.item_id, fields: page.fakes.map((f) => ({ key: f.key, label: f.label, value: f.real })) };
    write(path.join(siteDir, page.valuesPath.slice(1)), JSON.stringify(values, null, 2) + "\n");
  }
  if (poisonedPages.length) {
    const rows = poisonedPages.flatMap((p) => p.fakes.map((f) => ({ item_id: p.item_id, field: f.key, fake_value: f.fake })));
    fs.writeFileSync(fakesFile, JSON.stringify(rows, null, 2) + "\n");
  }

  const scoredFields =
    data.items.products.length * data.fields.product.length +
    data.items.articles.length * data.fields.article.length;
  const manifest = {
    condition,
    seed,
    scored_fields: scoredFields,
    ...(poisonedPages.length && { fakes_file: path.basename(fakesFile) }),
    pages: pages.map(({ path: p, file, type, item_id, seed: s, valuesPath }) => ({
      path: p,
      file,
      type,
      ...(item_id && { item_id }),
      seed: s,
      ...(valuesPath && { values: valuesPath }),
    })),
  };
  fs.writeFileSync(path.join(outDir, `${condition}.manifest.json`), JSON.stringify(manifest, null, 2) + "\n");
  return { siteDir, pages, manifest };
}

// Exported before the command-line part below runs, so a defense file that requires this module (the tarpit
// uses pageSeed and makeRng) gets the finished exports even when this file is the one being run.
module.exports = { availableConditions, loadData, loadDefense, buildPages, writeCondition, escapeHtml, pageSeed, makeRng, checkDefense, robotsTxt };

if (require.main === module) {
  const { parseArgs } = require("util");
  let parsed;
  try {
    parsed = parseArgs({ allowPositionals: true, options: { out: { type: "string" }, seed: { type: "string" } } });
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
  const condition = parsed.positionals[0];
  if (!condition) {
    console.error(`Usage: node site/generate.js <condition> [--out <dir>] [--seed <n>]   (built so far: ${availableConditions().join(", ")})`);
    process.exit(1);
  }
  try {
    const outDir = parsed.values.out ? path.resolve(parsed.values.out) : undefined;
    const seed = parsed.values.seed !== undefined ? Number(parsed.values.seed) : undefined;
    if (seed !== undefined && !Number.isInteger(seed)) throw new Error(`--seed must be a whole number, got "${parsed.values.seed}".`);
    const { siteDir, pages, manifest } = writeCondition(condition, outDir, seed);
    console.log(`Wrote ${pages.length} pages and robots.txt to ${path.relative(ROOT, siteDir)}/ (${manifest.scored_fields} scored fields)`);
    if (manifest.fakes_file) {
      const fakes = pages.reduce((n, p) => n + (p.fakes ? p.fakes.length : 0), 0);
      console.log(`Poisoned: ${fakes} fakes in ${path.relative(ROOT, path.join(path.dirname(siteDir), manifest.fakes_file))}, real values in ${path.relative(ROOT, siteDir)}/values/`);
    }
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

