"""Model timing for scraper (c): how fast is each local Ollama model on our pages?

    python measurement/time_models.py [--models gemma3:1b llama3.2:3b] [--pages /products/p1 /products/p2 /articles/a1]
                                      [--repeats 2] [--num-predict 400] [--out results/<date>-model-timing]

For each pulled model (default: every model Ollama has) and each page (default: 2 products and 1 article):
  1. takes the page's visible text from the generated baseline site with Playwright (no server needed),
  2. sends it to Ollama's /api/generate with a fixed timing prompt, temperature 0 and a cap on reply length,
  3. records Ollama's own timings (load, prompt reading, generating), the prompt and reply token counts,
     the wall-clock time, and how many of the page's real values appear anywhere in the reply.

Each model gets one unscored warm-up call first, so the model's load time is reported separately.
Model names, digests, sizes and quantization come from /api/tags, so the chosen model can be recorded exactly (§2).

This is measurement tooling (midterm §2), not scraper (c): the timing prompt below is a generic, fixed request used
only to compare speed. Scraper (c)'s own prompt, parsing and failure rules are written by Joseph.
"values found" is a rough check (does the real value appear in the reply as text?), not the scoring script.

Writes report.md, report.json and every raw reply (replies/) to the results folder.
"""

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_PAGES = ["/products/p1", "/products/p2", "/articles/a1"]
OLLAMA_URL = "http://127.0.0.1:11434"
NS = 1e9  # Ollama reports durations in nanoseconds

TIMING_PROMPT = (
    "Here is the text of one web page.\n\n{text}\n\n"
    "For each of these fields, give the value shown on the page: {labels}.\n"
    "Answer with one JSON object whose keys are the field names."
)


def list_models(base_url, timeout=30):
    """Pulled models from /api/tags: name, digest, size and details."""
    reply = requests.get(f"{base_url}/api/tags", timeout=timeout)
    reply.raise_for_status()
    models = []
    for m in reply.json().get("models", []):
        details = m.get("details") or {}
        models.append({
            "name": m.get("name") or m.get("model"),
            "digest": m.get("digest", ""),
            "size_bytes": m.get("size"),
            "parameter_size": details.get("parameter_size"),
            "quantization": details.get("quantization_level"),
            "family": details.get("family"),
        })
    return models


def build_prompt(text, labels):
    return TIMING_PROMPT.format(text=text.strip(), labels=", ".join(labels))


def page_targets(page_path, items, fields):
    """(labels, {label: real value}) for a product or article page path such as /products/p1."""
    kind, item_id = page_path.strip("/").split("/")
    if kind == "products":
        item = next(p for p in items["products"] if p["product_id"] == item_id)
        field_list = fields["product"]
    elif kind == "articles":
        item = next(a for a in items["articles"] if a["article_id"] == item_id)
        field_list = fields["article"]
    else:
        raise ValueError(f"{page_path} is not a product or article page")
    return [f["label"] for f in field_list], {f["label"]: str(item[f["key"]]) for f in field_list}


def values_found(reply_text, expected):
    """How many real values appear in the reply as text (case-insensitive). A rough quality signal only."""
    reply = reply_text.casefold()
    return sum(1 for value in expected.values() if value.casefold() in reply)


def page_texts(page_paths, condition="baseline", conditions_dir=None, executable_path=None):
    """Visible text (document.body.innerText) of each page, read from the generated files."""
    from playwright.sync_api import sync_playwright

    from measurement.screenshots import load_pages

    conditions_dir = Path(conditions_dir or ROOT / "conditions")
    files = {p["path"]: p["file"] for p in load_pages(condition, conditions_dir)}
    texts = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({"executable_path": executable_path} if executable_path else {}))
        page = browser.new_page()
        for path in page_paths:
            if path not in files:
                raise SystemExit(f"{path} is not a page of the {condition} site")
            page.goto((conditions_dir / condition / files[path]).resolve().as_uri(), wait_until="load")
            texts[path] = page.inner_text("body")
        browser.close()
    return texts


def generate(base_url, model, prompt, num_predict, timeout):
    """One non-streaming /api/generate call; returns Ollama's reply plus the wall-clock seconds."""
    start = time.perf_counter()
    reply = requests.post(f"{base_url}/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict},
    }, timeout=timeout)
    wall = time.perf_counter() - start
    reply.raise_for_status()
    return reply.json(), wall


def measurement(data, wall, expected):
    """The numbers kept from one call."""
    eval_count = data.get("eval_count") or 0
    eval_s = (data.get("eval_duration") or 0) / NS
    return {
        "wall_s": round(wall, 3),
        "total_s": round((data.get("total_duration") or 0) / NS, 3),
        "load_s": round((data.get("load_duration") or 0) / NS, 3),
        "prompt_tokens": data.get("prompt_eval_count") or 0,
        "prompt_s": round((data.get("prompt_eval_duration") or 0) / NS, 3),
        "reply_tokens": eval_count,
        "reply_s": round(eval_s, 3),
        "reply_tokens_per_s": round(eval_count / eval_s, 1) if eval_s else None,
        "values_found": values_found(data.get("response", ""), expected),
        "values_expected": len(expected),
    }


def summarize(model, calls):
    """Average per page over every scored call of one model."""
    ok = [c for c in calls if "error" not in c]
    def mean(key):
        vals = [c[key] for c in ok if c.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None
    return {
        "model": model,
        "calls": len(calls),
        "errors": len(calls) - len(ok),
        "mean_wall_s": mean("wall_s"),
        "mean_prompt_tokens": mean("prompt_tokens"),
        "mean_reply_tokens": mean("reply_tokens"),
        "mean_reply_tokens_per_s": mean("reply_tokens_per_s"),
        "values_found": sum(c["values_found"] for c in ok),
        "values_expected": sum(c["values_expected"] for c in ok),
    }


def write_report(out_dir, report):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Model timing for scraper (c)",
        "",
        f"Run {report['run_at']} · Ollama {report['ollama_version']} · pages {', '.join(report['pages'])} · "
        f"{report['repeats']} timed call(s) per page · reply capped at {report['num_predict']} tokens · temperature 0",
        "",
        "## Models",
        "",
        "| Model | Parameters | Quantization | Size | Digest | Load (s) |",
        "|---|---|---|---|---|---|",
    ]
    for m in report["models"]:
        size = f"{m['size_bytes'] / 1e9:.2f} GB" if m.get("size_bytes") else ""
        lines.append(f"| `{m['name']}` | {m.get('parameter_size') or ''} | {m.get('quantization') or ''} | {size} | "
                     f"`{(m.get('digest') or '')[:12]}` | {m.get('load_s', '')} |")
    lines += [
        "",
        "## Averages per page (warm model)",
        "",
        "| Model | Seconds per page | Prompt tokens | Reply tokens | Reply tokens/s | Values found in reply | Errors |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in report["summary"]:
        found = f"{s['values_found']}/{s['values_expected']}" if s["values_expected"] else "—"
        lines.append(f"| `{s['model']}` | {s['mean_wall_s']} | {s['mean_prompt_tokens']} | {s['mean_reply_tokens']} | "
                     f"{s['mean_reply_tokens_per_s']} | {found} | {s['errors']} |")
    lines += [
        "",
        "## Every call",
        "",
        "| Model | Page | Repeat | Wall (s) | Prompt tokens | Prompt (s) | Reply tokens | Reply (s) | Values found |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in report["calls"]:
        if "error" in c:
            lines.append(f"| `{c['model']}` | {c['page']} | {c['repeat']} | error: {c['error'][:80]} | | | | | |")
            continue
        lines.append(f"| `{c['model']}` | {c['page']} | {c['repeat']} | {c['wall_s']} | {c['prompt_tokens']} | {c['prompt_s']} | "
                     f"{c['reply_tokens']} | {c['reply_s']} | {c['values_found']}/{c['values_expected']} |")
    est = [s for s in report["summary"] if s["mean_wall_s"]]
    if est:
        lines += ["", "**Estimated time for scraper (c):** 10 pages × 3 runs × 3 conditions = 90 page calls.", ""]
        for s in est:
            lines.append(f"- `{s['model']}`: about {round(s['mean_wall_s'] * 90 / 60, 1)} minutes.")
    lines += [
        "",
        "The timing prompt is a fixed, generic request used only to compare speed; scraper (c)'s own prompt is written separately. "
        "\"Values found\" counts real values that appear anywhere in the reply: a rough quality signal, not a score. "
        "Raw replies are in `replies/`.",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Time local Ollama models on the test site's pages (for scraper (c))")
    parser.add_argument("--models", nargs="+", help="models to time (default: every model Ollama has pulled)")
    parser.add_argument("--pages", nargs="+", default=DEFAULT_PAGES, help="page paths (default: 2 products, 1 article)")
    parser.add_argument("--condition", default="baseline", help="site version to read the pages from (default baseline)")
    parser.add_argument("--repeats", type=int, default=2, help="timed calls per page and model (default 2)")
    parser.add_argument("--num-predict", type=int, default=400, help="cap on reply tokens (default 400)")
    parser.add_argument("--timeout", type=float, default=600, help="seconds to wait for one reply (default 600)")
    parser.add_argument("--ollama-url", default=OLLAMA_URL, help=f"Ollama address (default {OLLAMA_URL})")
    parser.add_argument("--out", help="results folder (default results/<today>-model-timing)")
    parser.add_argument("--executable-path", help="a Chromium binary to use instead of Playwright's own")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else ROOT / "results" / f"{datetime.date.today().isoformat()}-model-timing"
    (out_dir / "replies").mkdir(parents=True, exist_ok=True)

    try:
        version = requests.get(f"{args.ollama_url}/api/version", timeout=10).json().get("version", "unknown")
        available = list_models(args.ollama_url)
    except requests.exceptions.RequestException as err:
        raise SystemExit(f"Could not reach Ollama at {args.ollama_url} ({err}). Is the Ollama app running?")
    by_name = {m["name"]: m for m in available}
    names = args.models or [m["name"] for m in available]
    missing = [n for n in names if n not in by_name]
    if missing:
        raise SystemExit(f"Not pulled: {', '.join(missing)}. Pulled: {', '.join(by_name) or 'none'}. Run: ollama pull <model>")
    if not names:
        raise SystemExit("Ollama has no models. Run: ollama pull <model>")

    from measurement.test4 import generate as generate_site
    generate_site(args.condition)
    items = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    fields = json.loads((ROOT / "data" / "fields.json").read_text(encoding="utf-8"))
    print(f"Reading the text of {len(args.pages)} {args.condition} pages ...")
    texts = page_texts(args.pages, args.condition, executable_path=args.executable_path)

    models, calls = [], []
    for name in names:
        info = dict(by_name[name])
        labels, expected = page_targets(args.pages[0], items, fields)
        print(f"{name}: warm-up call (loads the model) ...")
        try:
            data, wall = generate(args.ollama_url, name, build_prompt(texts[args.pages[0]], labels), args.num_predict, args.timeout)
            info["load_s"] = round((data.get("load_duration") or 0) / NS, 3)
            info["warmup_wall_s"] = round(wall, 3)
        except requests.exceptions.RequestException as err:
            info["load_s"] = f"error: {err}"
        models.append(info)
        for path in args.pages:
            labels, expected = page_targets(path, items, fields)
            prompt = build_prompt(texts[path], labels)
            for repeat in range(1, args.repeats + 1):
                print(f"  {name} {path} #{repeat} ...")
                call = {"model": name, "page": path, "repeat": repeat}
                try:
                    data, wall = generate(args.ollama_url, name, prompt, args.num_predict, args.timeout)
                    call.update(measurement(data, wall, expected))
                    reply_file = out_dir / "replies" / f"{name.replace(':', '_').replace('/', '_')}{path.replace('/', '_')}-{repeat}.txt"
                    reply_file.write_text(data.get("response", ""), encoding="utf-8")
                except requests.exceptions.RequestException as err:
                    call["error"] = str(err)
                calls.append(call)

    report = {
        "test": "model timing for scraper (c)",
        "run_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "ollama_version": version,
        "condition": args.condition,
        "pages": args.pages,
        "repeats": args.repeats,
        "num_predict": args.num_predict,
        "timing_prompt": TIMING_PROMPT,
        "models": models,
        "calls": calls,
        "summary": [summarize(n, [c for c in calls if c["model"] == n]) for n in names],
    }
    write_report(out_dir, report)
    print()
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
