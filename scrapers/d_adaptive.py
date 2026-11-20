# Scraper (d): adaptive. Same inputs, crawl and output as (b), plus the three abilities from the midterm (§2):
#   1. wait until the page has had no changes for 3 s (10 s at most), which beats poisoning's 2 s swap;
#   2. ignore everything computed style hides, hidden links included, which skips the honeypot's trap link;
#   3. sort the field elements by their computed CSS order, then use the same label-plus-next rule as (a) and (b),
#      which reads shuffled pages in on-screen order.
# Written with Claude: Joseph copied (b) and added part 1 with lines Claude supplied (D98); at Joseph's request
# Claude wrote part 2 (D99). Both are disclosed in Claude-chat-keeper.md.
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
#Playwright drives a real Chromium browser; the other imports are the same as (a)
import requests #everything including this and below is from scraper (a)
from urllib.parse import urljoin, urlparse
import argparse
from urllib.robotparser import RobotFileParser
import time
from datetime import datetime, timezone

WAIT_FOR_QUIET = """
([quietMs, timeoutMs]) => new Promise((resolve) => {
  const start = performance.now();
  let quiet = setTimeout(() => done(false), quietMs);            // fires after quietMs with no changes
  const observer = new MutationObserver(() => {                  // any change restarts the quiet timer
    clearTimeout(quiet);
    quiet = setTimeout(() => done(false), quietMs);
  });
  observer.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
  const limit = setTimeout(() => done(true), timeoutMs);         // never wait longer than timeoutMs
  function done(timedOut) {
    observer.disconnect(); clearTimeout(quiet); clearTimeout(limit);
    resolve({ timedOut: timedOut, waitedMs: Math.round(performance.now() - start) });
  }
})
"""

# Runs in the page after the wait. For each label: find the visible element whose text is exactly the label, take the
# visible elements that share its parent, sort them by computed CSS order (ties keep their HTML order), and return the
# text of the element right after the label. Also returns the href of every link that computed style shows.
READ_VISIBLE_PAGE = """
(labels) => {
  const hidden = (el) => {
    if (getComputedStyle(el).visibility !== "visible") return true;               // visibility: hidden (it is inherited)
    for (let n = el; n; n = n.parentElement) {
      if (getComputedStyle(n).display === "none") return true;                   // display: none on it or on a parent
    }
    return false;
  };
  const elements = Array.from(document.body.querySelectorAll("*"));
  const fields = {};
  for (const label of labels) {
    const labelEl = elements.find((el) => el.children.length === 0 && el.textContent.trim() === label && !hidden(el));
    if (!labelEl || !labelEl.parentElement) continue;
    const onScreen = Array.from(labelEl.parentElement.children)
      .filter((el) => !hidden(el))
      .map((el, i) => ({ el: el, i: i, order: Number(getComputedStyle(el).order) || 0 }))
      .sort((a, b) => a.order - b.order || a.i - b.i);
    const at = onScreen.findIndex((x) => x.el === labelEl);
    if (at >= 0 && at + 1 < onScreen.length) fields[label] = onScreen[at + 1].el.textContent.trim();
  }
  const links = Array.from(document.querySelectorAll("a[href]")).filter((a) => !hidden(a)).map((a) => a.getAttribute("href"));
  return { fields: fields, links: links };
}
"""

config = json.load(open("config.json"))
quiet_ms = config["adaptive_quiet_seconds"] * 1000      # 3000
timeout_ms = config["adaptive_timeout_seconds"] * 1000  # 10000

parser = argparse.ArgumentParser(description="Scraper (d): adaptive")
parser.add_argument("--start-url", default="http://127.0.0.1:3000/") #default url to scrape, can be changed with command line argument
parser.add_argument("--page-cap", type=int, default=15) #max pages to scrape
parser.add_argument("--robots", choices=["obey", "ignore"], default="obey") #two choices obey and ignore
parser.add_argument("--run-id", required=True) # run id is required, tells the server whos asking
parser.add_argument("--out", required=True)# output file is required, where the scraped data will be saved
args = parser.parse_args()

start_url = args.start_url #where the crawl starts
page_cap = args.page_cap #max pages to scrape
user_agent = f"run={args.run_id}" #user agent is the run id, tells the server whos asking

robots_url = urljoin(start_url, "/robots.txt")
rules = RobotFileParser()
try:
    robots_response = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=5)
    rules.parse(robots_response.text.splitlines())
except requests.exceptions.RequestException:
    print("could not read robots.txt; treating every page as allowed")
    rules.parse([])

pages = [] #pages scraped
records = [] #holds the field values found, not the pages

queue = [start_url] #list of urls to scrape
visited = set() #set of urls already scraped 

labels = json.load(open("data/fields.json")) #opening fields json file to get the labels for the fields we want to scrape
all_fields = labels["product"] + labels["article"] #setting all_fields to be both product and article from json

print(start_url, page_cap, user_agent, queue)


with sync_playwright() as p: #launching playwright to use a browser to scrape the page after js load
    browser = p.chromium.launch()
    page = browser.new_page(user_agent=user_agent)
    started_at = datetime.now(timezone.utc).isoformat() #wwhen the run started

    start_time = time.time() #time start

    while queue and len(visited) < page_cap: #while there are urls in the queue and we have not reached the page cap
        url = queue.pop(0) #get the first url in the queue
        if url in visited:
            continue
        visited.add(url)
        if args.robots == "obey" and not rules.can_fetch(user_agent, url):
            print("skipped (robots.txt):", url)
            continue

        path = urlparse(url).path #get the path of the url
        try:
            response = page.goto(url, wait_until="load", timeout=5000) #load the page in the browser, wait for the load event, give up after 5000 ms (5 s)
        except PlaywrightTimeout:
            print("timeout", url)
            pages.append({"path": path, "status": None, "error": "timeout"}) #if timeout, add to pages with error
            continue
        except PlaywrightError:
            print("connection error", url)
            pages.append({"path": path, "status": None, "error": "connection_error"}) #any other browser error (e.g. the server is down): save it and move on
            continue

        print(response.status, url)
        pages.append({"path": path, "status": response.status, "error": None}) #append the page to pages with status and no error


        wait = page.evaluate(WAIT_FOR_QUIET, [quiet_ms, timeout_ms])
        if wait["timedOut"]:
            print("quiet wait timed out after", wait["waitedMs"], "ms, reading the page as it is", url)
        else:
            print("page quiet after", wait["waitedMs"], "ms", url)


        seen = page.evaluate(READ_VISIBLE_PAGE, [field["label"] for field in all_fields]) #read the live page, as shown on screen
        for field in all_fields:
            if field["label"] in seen["fields"]:     # label found, and a visible element follows it in CSS order
                records.append({"page": path, "field": field["key"], "value": seen["fields"][field["label"]]})
        for href in seen["links"]:                   # visible links only, so a hidden trap link is never followed
            link = urljoin(url, href)
            same_site = urlparse(link).netloc == urlparse(start_url).netloc
            if same_site and link not in visited and link not in queue:
                queue.append(link)                   # wait in line to be visited
    seconds = round(time.time() - start_time, 3)
    browser.close()


output = {
    "run": {
        "run_id": args.run_id,
        "scraper": "d",
        "start_url": start_url,
        "page_cap": page_cap,
        "obey_robots_txt": args.robots == "obey",
        "started_at": started_at,
        "seconds": seconds,
    },
    "pages": pages,
    "records": records,
}
with open(args.out, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)
print(len(records), "records written to", args.out)


# How (d) differs from (b): (b) reads page.content() with BeautifulSoup, a static copy of the HTML, so it sees the
# source order and every element, hidden or not. (d) asks the live browser instead (getComputedStyle), so it sees
# what a visitor sees: the CSS order and which elements are hidden. That is the capability the shuffling defense and
# the honeypot target, so the midterm's hypothesis expects (d) to be unaffected by both, and by poisoning thanks to
# the wait.
