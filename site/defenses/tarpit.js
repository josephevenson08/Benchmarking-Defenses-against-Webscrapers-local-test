//tarpit file, tarpit is practically just wasting the scrapers time sending it down a maze of follow links

const { pageSeed, makeRng } = require("../generate");
const config = require("../../config.json");
const SENTENCES = [                     // ← put your list back here
  "this is a maze",
  "this is a path",
  "this is a another",
  "this is a this is it",
];

function footer(page, rng) { //calls once for each of the 10 pages
    return `<a href="/maze/start">Archive</a>`;
}

const disallow = ["/maze/"];

function maze(req, res) {
    const rng = makeRng(pageSeed(config.seed, "tarpit", req.path));
    const items = [];
    for (let i = 0; i < 5; i++) {
        const id = Math.floor(rng() * 4294967296).toString(16);
        items.push(`<li><a href="/maze/${id}">next</a></li>`);
    }
    const first = SENTENCES[Math.floor(rng() * SENTENCES.length)];       // ← these three lines
    const second = SENTENCES[Math.floor(rng() * SENTENCES.length)];      //   move here, and replace
    const html = "<p>" + first + ". " + second + ".</p><ul>" + items.join("") + "</ul>";   //   the old html line
    setTimeout(() => {
        res.locals.log = { tarpit: true, maze_hash: req.params.hash };
        res.type("html").send(html);
    }, 2000);                                   // answers after 2 seconds
}

module.exports = { footer, disallow, maze };