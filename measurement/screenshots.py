"""Takes one full-page screenshot of every page of a generated condition.

    python measurement/screenshots.py <condition> --out <folder> [--wait 3] [--width 1280] [--height 800]

Reads the page list from conditions/<condition>.manifest.json (written by the
generator; scrapers never read it) and opens each page straight from
conditions/<condition>/ in headless Chromium. No server is needed, and the
request log stays clean. Before each screenshot it waits --wait seconds after
the load event (midterm §5: screenshots are taken after a 3-second wait, so
poisoned pages show their real values).

Files are named after the page path: index.png, products.png,
products-p1.png, articles-a1.png. Compare two folders with
measurement/pixel_diff.mjs.
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def png_name(page_path):
    """'/' -> index.png, '/products/' -> products.png, '/products/p1' -> products-p1.png."""
    name = page_path.strip("/").replace("/", "-")
    return (name or "index") + ".png"


def load_pages(condition, conditions_dir):
    manifest_file = Path(conditions_dir) / f"{condition}.manifest.json"
    if not manifest_file.exists():
        raise SystemExit(f"No manifest at {manifest_file}. Run: npm run generate -- {condition}")
    pages = json.loads(manifest_file.read_text(encoding="utf-8"))["pages"]
    if any("file" not in page for page in pages):
        raise SystemExit(f"{manifest_file} is from an older generator. Run: npm run generate -- {condition}")
    return pages


def take_screenshots(condition, out_dir, wait=3.0, width=1280, height=800,
                     conditions_dir=None, executable_path=None):
    conditions_dir = Path(conditions_dir or ROOT / "conditions")
    pages = load_pages(condition, conditions_dir)
    site_dir = conditions_dir / condition
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with sync_playwright() as p:
        launch = {"executable_path": executable_path} if executable_path else {}
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for entry in pages:
            page.goto((site_dir / entry["file"]).resolve().as_uri(), wait_until="load")
            page.wait_for_timeout(wait * 1000)
            target = out_dir / png_name(entry["path"])
            page.screenshot(path=str(target), full_page=True)
            written.append(target)
        browser.close()
    return written


def main():
    parser = argparse.ArgumentParser(description="Full-page screenshots of one generated condition")
    parser.add_argument("condition", help="for example baseline or shuffled")
    parser.add_argument("--out", required=True, help="folder for the PNG files")
    parser.add_argument("--wait", type=float, default=3.0, help="seconds to wait after load (default 3)")
    parser.add_argument("--width", type=int, default=1280, help="viewport width in pixels (default 1280)")
    parser.add_argument("--height", type=int, default=800, help="viewport height in pixels (default 800)")
    parser.add_argument("--executable-path", help="a Chromium binary to use instead of Playwright's own")
    args = parser.parse_args()
    written = take_screenshots(args.condition, args.out, args.wait, args.width, args.height,
                               executable_path=args.executable_path)
    for path in written:
        print(path)
    print(len(written), "screenshots written to", args.out)


if __name__ == "__main__":
    main()
