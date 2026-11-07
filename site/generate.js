// Builds one condition of the test site from the data list.
//
//   node site/generate.js baseline
//   node site/generate.js shuffled      (once site/defenses/shuffled.js exists)
//
// Writes the 10 pages and robots.txt to conditions/<condition>/, and a manifest
// of the pages to conditions/<condition>.manifest.json. The manifest sits
// outside the served folder so scrapers can't fetch it.
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
function loadDefense(condition) {
  if (condition === "baseline") return null;
  const defense = require(path.join(DEFENSES_DIR, `${condition}.js`));
  if (defense.style !== undefined && typeof defense.style !== "string") {
    throw new Error(`site/defenses/${condition}.js: "style" must be a string of CSS.`);
  }
  if (defense.fieldRows !== undefined && typeof defense.fieldRows !== "function") {
    throw new Error(`site/defenses/${condition}.js: "fieldRows" must be a function (rows, rng).`);
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

function layout(title, main, extraStyle = "") {
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
  <footer>Synthetic test site for a local scraping study. All content is made up.</footer>
</body>
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
  return defense.fieldRows(rows, rng);
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
  const page = (title, main) => layout(title, main, style);
  const fieldsFor = (pagePath, item, fieldList) => fieldsBlock(item, fieldList, defense, makeRng(seedFor(pagePath)));

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
${linkList(articles.map((a) => ({ href: `/articles/${a.id}`, text: `Article ${a.n}` })))}`
      ),
    },
    {
      path: "/products/",
      file: "products/index.html",
      type: "category",
      html: page(
        "Products",
        `    <h1>Products</h1>
${linkList(products.map((p) => ({ href: `/products/${p.id}`, text: `Product ${p.n}` })))}`
      ),
    },
  ];

  for (const p of products) {
    const pagePath = `/products/${p.id}`;
    pages.push({
      path: pagePath,
      file: `products/${p.id}.html`,
      type: "product",
      item_id: p.id,
      html: page(`Product ${p.n}`, `    <h1>Product details</h1>\n${fieldsFor(pagePath, p.item, fields.product)}`),
    });
  }
  for (const a of articles) {
    const pagePath = `/articles/${a.id}`;
    pages.push({
      path: pagePath,
      file: `articles/${a.id}.html`,
      type: "article",
      item_id: a.id,
      html: page(`Article ${a.n}`, `    <h1>Article</h1>\n${fieldsFor(pagePath, a.item, fields.article)}`),
    });
  }
  for (const pg of pages) pg.seed = seedFor(pg.path);
  return pages;
}

const ROBOTS_TXT = "User-agent: *\nDisallow:\n";

function writeCondition(condition, outDir = path.join(ROOT, "conditions"), seed = loadConfig().seed) {
  const available = availableConditions();
  if (!available.includes(condition)) {
    throw new Error(`Unknown or not-yet-built condition "${condition}". Built so far: ${available.join(", ")}.`);
  }
  const data = loadData();
  const pages = buildPages(data, { condition, defense: loadDefense(condition), seed });
  const siteDir = path.join(outDir, condition);

  fs.rmSync(siteDir, { recursive: true, force: true });
  for (const page of pages) {
    const file = path.join(siteDir, page.file);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, page.html);
  }
  fs.writeFileSync(path.join(siteDir, "robots.txt"), ROBOTS_TXT);

  const scoredFields =
    data.items.products.length * data.fields.product.length +
    data.items.articles.length * data.fields.article.length;
  const manifest = {
    condition,
    seed,
    scored_fields: scoredFields,
    pages: pages.map(({ path: p, type, item_id, seed: s }) => ({ path: p, type, ...(item_id && { item_id }), seed: s })),
  };
  fs.writeFileSync(path.join(outDir, `${condition}.manifest.json`), JSON.stringify(manifest, null, 2) + "\n");
  return { siteDir, pages, manifest };
}

if (require.main === module) {
  const condition = process.argv[2];
  if (!condition) {
    console.error(`Usage: node site/generate.js <condition>   (built so far: ${availableConditions().join(", ")})`);
    process.exit(1);
  }
  try {
    const { siteDir, pages, manifest } = writeCondition(condition);
    console.log(`Wrote ${pages.length} pages and robots.txt to ${path.relative(ROOT, siteDir)}/ (${manifest.scored_fields} scored fields)`);
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

module.exports = { availableConditions, loadData, buildPages, writeCondition, escapeHtml, pageSeed, makeRng };
