// Builds one condition of the test site from the data list.
//
//   node site/generate.js baseline
//
// Writes the 10 pages and robots.txt to conditions/<condition>/, and a manifest
// of the pages to conditions/<condition>.manifest.json. The manifest sits
// outside the served folder so scrapers can't fetch it.
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const SITE_NAME = "Demo Shop";

// Only the baseline exists so far; each defense adds its condition here.
const CONDITIONS = ["baseline"];

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

function layout(title, main) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} · ${SITE_NAME}</title>
  <style>${STYLE}
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

function linkList(links) {
  const items = links.map((l) => `      <li><a href="${l.href}">${escapeHtml(l.text)}</a></li>`);
  return `    <ul>\n${items.join("\n")}\n    </ul>`;
}

// Link text and titles use "Product 1", "Article 1" and so on, never a scored
// value, so each value appears only in its own row on its own page.
function buildPages({ items, fields }) {
  const products = items.products.map((p, i) => ({ item: p, id: p.product_id, n: i + 1 }));
  const articles = items.articles.map((a, i) => ({ item: a, id: a.article_id, n: i + 1 }));

  const pages = [
    {
      path: "/",
      file: "index.html",
      type: "home",
      html: layout(
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
      html: layout(
        "Products",
        `    <h1>Products</h1>
${linkList(products.map((p) => ({ href: `/products/${p.id}`, text: `Product ${p.n}` })))}`
      ),
    },
  ];

  for (const p of products) {
    pages.push({
      path: `/products/${p.id}`,
      file: `products/${p.id}.html`,
      type: "product",
      item_id: p.id,
      html: layout(`Product ${p.n}`, `    <h1>Product details</h1>\n${fieldRows(p.item, fields.product)}`),
    });
  }
  for (const a of articles) {
    pages.push({
      path: `/articles/${a.id}`,
      file: `articles/${a.id}.html`,
      type: "article",
      item_id: a.id,
      html: layout(`Article ${a.n}`, `    <h1>Article</h1>\n${fieldRows(a.item, fields.article)}`),
    });
  }
  return pages;
}

const ROBOTS_TXT = "User-agent: *\nDisallow:\n";

function writeCondition(condition, outDir = path.join(ROOT, "conditions")) {
  if (!CONDITIONS.includes(condition)) {
    throw new Error(`Unknown or not-yet-built condition "${condition}". Built so far: ${CONDITIONS.join(", ")}.`);
  }
  const data = loadData();
  const pages = buildPages(data);
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
    scored_fields: scoredFields,
    pages: pages.map(({ path: p, type, item_id }) => ({ path: p, type, ...(item_id && { item_id }) })),
  };
  fs.writeFileSync(path.join(outDir, `${condition}.manifest.json`), JSON.stringify(manifest, null, 2) + "\n");
  return { siteDir, pages, manifest };
}

if (require.main === module) {
  const condition = process.argv[2];
  if (!condition) {
    console.error(`Usage: node site/generate.js <condition>   (built so far: ${CONDITIONS.join(", ")})`);
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

module.exports = { CONDITIONS, loadData, buildPages, writeCondition, escapeHtml };
