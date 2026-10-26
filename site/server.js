// Serves one generated condition of the test site on localhost and logs every
// request as one JSON line.
//
//   node site/server.js baseline [--port 3000] [--log logs/requests.jsonl]
//
// Scrapers put their run ID in the User-Agent as "run=<id>", e.g.
// "bench-scraper (run=a-baseline-1)". Requests without one log as "unknown".
const fs = require("fs");
const path = require("path");
const { parseArgs } = require("util");
const express = require("express");

const ROOT = path.join(__dirname, "..");
const RUN_ID = /\brun=([^\s;()]+)/;

function runIdFrom(userAgent) {
  const match = userAgent && userAgent.match(RUN_ID);
  return match ? match[1] : "unknown";
}

// One line per request with the RequestLog fields from the data model, plus
// the raw User-Agent for debugging.
function requestLogger(logFile, trapPath) {
  fs.mkdirSync(path.dirname(logFile), { recursive: true });
  return (req, res, next) => {
    const timestamp = new Date().toISOString();
    const start = process.hrtime.bigint();
    res.on("finish", () => {
      const userAgent = req.get("user-agent") ?? null;
      const entry = {
        timestamp,
        run_id: runIdFrom(userAgent),
        path: req.originalUrl,
        status: res.statusCode,
        response_ms: Math.round(Number(process.hrtime.bigint() - start) / 1e3) / 1e3,
        honeypot_hit: req.path === trapPath,
        user_agent: userAgent,
      };
      fs.appendFileSync(logFile, JSON.stringify(entry) + "\n");
    });
    next();
  };
}

function createApp({ siteDir, logFile, trapPath }) {
  const app = express();
  app.disable("x-powered-by");
  app.disable("etag");
  app.use(requestLogger(logFile, trapPath));

  // Nothing links here until the honeypot defense adds its hidden link.
  app.get(trapPath, (req, res) => {
    res.type("html").send("<!doctype html>\n<title>Archive</title>\n<p>Nothing here.</p>\n");
  });

  // No caching headers, so every request gets a full 200 and a log line.
  app.use(
    express.static(siteDir, { extensions: ["html"], etag: false, lastModified: false, cacheControl: false })
  );
  app.use((req, res) => res.status(404).type("text").send("Not found\n"));
  return app;
}

if (require.main === module) {
  const config = JSON.parse(fs.readFileSync(path.join(ROOT, "config.json"), "utf8"));
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      port: { type: "string", default: String(config.port) },
      log: { type: "string", default: "logs/requests.jsonl" },
    },
  });
  const condition = positionals[0];
  if (!condition) {
    console.error("Usage: node site/server.js <condition> [--port 3000] [--log logs/requests.jsonl]");
    process.exit(1);
  }
  const siteDir = path.join(ROOT, "conditions", condition);
  if (!fs.existsSync(siteDir)) {
    console.error(`No generated site at conditions/${condition}/. Run: npm run generate -- ${condition}`);
    process.exit(1);
  }
  const logFile = path.resolve(ROOT, values.log);
  const app = createApp({ siteDir, logFile, trapPath: config.trap_path });
  // Bound to 127.0.0.1 so the site is reachable only from this machine.
  app.listen(Number(values.port), "127.0.0.1", (err) => {
    if (err) throw err;
    console.log(`Serving conditions/${condition}/ at http://localhost:${values.port}/`);
    console.log(`Logging requests to ${path.relative(ROOT, logFile)}`);
  });
}

module.exports = { createApp, runIdFrom };
