import json
from bs4 import BeautifulSoup
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


        soup = BeautifulSoup(page.content(), "html.parser") #build the tree after js load
        for field in all_fields:
            label_element = soup.find(string=field["label"])
            if label_element:
                value_element = label_element.parent.find_next_sibling() #step to the next element (the value)
                if value_element:
                    records.append({"page": path, "field": field["key"], "value": value_element.get_text(strip=True)})
        for a in soup.find_all("a"):                 # every link, hidden ones too
            link = urljoin(url, a.get("href", ""))   
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


# A BeautifulSoup tree is a representation of the HTML structure of a webpage,
# allowing for easy navigation and extraction of data from the HTML elements.
#
# Its structure is hierarchical, with the root element at the top and child elements
# nested within parent elements.
#
# It is very similar to the browser's DOM tree, which is also a tree of the page's
# HTML elements. The difference: BeautifulSoup's tree is a static copy of the HTML
# text, while the browser's DOM is live. It knows the CSS, the layout and which
# elements are visible.
#
# Why I used BeautifulSoup on page.content() instead of the live DOM: it lets (b)
# reuse scraper (a)'s exact rule (find the label, take the next element). That way
# (a) and (b) differ in only one thing: in (b) the page's scripts have run. This
# keeps the comparison between them fair.
#
# The catch: BeautifulSoup only sees the HTML, not the CSS order or which elements
# are hidden. That's why DOM shuffling and the honeypot link still work against (b).
# Scraper (d) will use the live DOM to get around that.
#
# I worked out this design with Claude (decision D51 in Claude-chat-keeper.md):
# Claude recommended reusing (a)'s rule on the HTML after load, and I chose it over
# reading only the visible text.