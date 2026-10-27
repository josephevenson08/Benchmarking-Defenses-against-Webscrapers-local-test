# Notes for Claude

This repository is Joseph Evenson's Blue Track research project. The plan it follows is the midterm, *Project Midterm Deliverable: Architecture, Design, and Evaluation Plan*. `README.md` summarizes it.

## Keep the Claude chat-keeper updated every turn

`Claude-chat-keeper.md` is the traceable record of AI use in this project. Every turn:

1. **Make sure the turn has an entry at the bottom of the turn log** with Joseph's prompt word for word. The UserPromptSubmit hook normally adds it. If it didn't, copy the prompt in exactly as sent, typos included.
2. **Fill the entry in:**
   - what Claude did (files, checks, commits);
   - a summary of Claude's answer;
   - the questions Claude asked, with their options and answers;
   - the direction chosen, by decision ID.
3. **Update the Decision register.** For each decision, give its basis in the midterm (cite the section, figure or test) and a fit label: Follows, Interprets, Adds or Deviates. Never present a deviation as following the plan.
4. **Update the Questions register and Open items.**
5. **Delete the pending marker line** the hook added.
6. **Commit and push the log with the turn's other work.**

## Keep GitHub in sync (Joseph's request, Turn 30; D40, D41)

Joseph works on `main`, on his laptop in VS Code. Claude works on `claude/quirky-curie-8j4nye`.

- **Before building on Joseph's files:** fetch, then merge `origin/main` into the branch. Merge only: never rebase, force-push or reset.
- **When Joseph needs something on `main`:** open a pull request from the branch into `main` (Joseph approved this) and tell Joseph plainly:

  > ⚠️ **Merge needed:** <link>, plus what is in it

  This applies when:
  - Claude finishes something Joseph will use on his laptop (for example the scoring script);
  - a milestone check passes;
  - a working session ends with changes not yet on `main`.
- **When `main` has nothing new to receive,** say so if Joseph asks.
- **After Joseph merges:** fetch, and merge `main` into the branch again.

## AI-use boundaries from the midterm (§2 "AI assistance", §7 "AI-agent plan")

- **Claude may draft:**
  - the test site (data list, page generator, Express server, request logger);
  - the measurement tooling (scoring script, experiment runner, user-cost runner);
  - the setup for scraper (e) (model choice and request format).
- **Joseph writes, and Claude must not write:**
  - the page defenses (shuffling, honeypot, poisoning);
  - the tarpit route;
  - scrapers (a)–(d);
  - the prompt, parsing and failure rules for (e).

  Claude may explain concepts and show small standalone examples that are not project code.
- **Scoring script:** Joseph writes the Test 2 fixture (63 correct, 4 wrong, 3 missing → accuracy 0.90, fake-value rate 2/70) *before* Claude writes any scoring code. Use the prompt from the midterm's AI-agent plan.
- **Scrapers must never read `data/items.json`.** It is the answer key. They may read `data/fields.json`.
- **Approved contracts:** the scraper output format, the scraper inputs and the scoring matching rules are in `docs/scraper-output.md`. Joseph approved them in Turn 9. Don't change them without Joseph's approval and a chat-keeper entry.
