// Stop hook: keeps Claude from ending a turn while Claude-chat-keeper.md still
// has a turn marked pending.
const fs = require("fs");
const path = require("path");

const PENDING_LINE = /^<!-- chat-keeper:pending -->$/m;

let raw = "";
process.stdin.on("data", (chunk) => (raw += chunk));
process.stdin.on("end", () => {
  let input;
  try {
    input = JSON.parse(raw || "{}");
  } catch {
    return;
  }
  // Already blocked once this turn: let it end rather than loop.
  if (input.stop_hook_active) return;

  const root = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
  const file = path.join(root, "Claude-chat-keeper.md");
  if (!fs.existsSync(file)) return;
  if (!PENDING_LINE.test(fs.readFileSync(file, "utf8"))) return;

  console.log(
    JSON.stringify({
      decision: "block",
      reason:
        "Claude-chat-keeper.md has a turn marked pending. Fill it in (questions asked, " +
        "what was done, Claude's answer, direction chosen and its basis in the midterm), " +
        "update the registers at the top, delete the pending marker line, then commit and push.",
    })
  );
});
