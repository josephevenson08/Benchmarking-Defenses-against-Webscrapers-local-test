// UserPromptSubmit hook: appends the prompt, word for word, as a new turn in
// Claude-chat-keeper.md and marks the turn pending until Claude fills it in.
const fs = require("fs");
const path = require("path");

const PENDING = "<!-- chat-keeper:pending -->";

let raw = "";
process.stdin.on("data", (chunk) => (raw += chunk));
process.stdin.on("end", () => {
  let input;
  try {
    input = JSON.parse(raw || "{}");
  } catch {
    return;
  }
  const prompt = (input.prompt || "").trim();
  if (!prompt) return;

  const root = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
  const file = path.join(root, "Claude-chat-keeper.md");
  if (!fs.existsSync(file)) return;

  const text = fs.readFileSync(file, "utf8");
  const numbers = [...text.matchAll(/^### Turn (\d+)/gm)].map((m) => Number(m[1]));
  const turn = numbers.length ? Math.max(...numbers) + 1 : 1;
  const stamp = new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC";
  const quoted = prompt
    .split(/\r?\n/)
    .map((line) => (line ? "> " + line : ">"))
    .join("\n");

  const entry =
    `\n### Turn ${turn} — ${stamp}\n\n` +
    `**Joseph's prompt (verbatim, captured by hook):**\n\n${quoted}\n\n${PENDING}\n`;
  fs.appendFileSync(file, (text.endsWith("\n") ? "" : "\n") + entry);
});
