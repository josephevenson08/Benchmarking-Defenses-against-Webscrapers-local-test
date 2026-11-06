import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
#all three imports needed for this scraper so that it can scrap after js load
import requests #everything including this and below is from scraper (a)
from urllib.parse import urljoin, urlparse
import argparse
from urllib.robotparser import RobotFileParser
import time
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description="Scraper (b): browser")
parser.add_argument("--start-url", default="http://127.0.0.1:3000/") #default url to scrape, can be changed with command line argument
parser.add_argument("--page-cap", type=int, default=15) #max pages to scrape
parser.add_argument("--robots", choices=["obey", "ignore"], default="obey") #two choices obey and ignore
parser.add_argument("--run-id", required=True) # run id is required, tells the server whos asking
parser.add_argument("--out", required=True)# output file is required, where the scraped data will be saved
args = parser.parse_args()

start_url = args.start_url
page_cap = args.page_cap
user_agent = f"run={args.run_id}"


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


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(user_agent=user_agent)
    started_at = datetime.now(timezone.utc).isoformat() #where we started at

    start_time = time.time() #time start

    while queue and len(visited) < page_cap:
        url = queue.pop(0) #get the first url in the queue
        if url in visited:
            continue
        visited.add(url)
        if args.robots == "obey" and not rules.can_fetch(user_agent, url):
            print("skipped (robots.txt):", url)
            continue

        path = urlparse(url).path
        try:
            response = page.goto(url, wait_until="load", timeout=5000)
        except PlaywrightTimeout:
            print("timeout", url)
            pages.append({"path": path, "status": None, "error": "timeout"})
            continue
        except PlaywrightError:
            print("connection error", url)
            pages.append({"path": path, "status": None, "error": "connection_error"})
            continue

        print(response.status, url)
        pages.append({"path": path, "status": response.status, "error": None})

        soup = BeautifulSoup(page.content(), "html.parser")
        for field in all_fields:
            label_element = soup.find(string=field["label"])
            if label_element:
                value_element = label_element.parent.find_next_sibling()
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
        "scraper": "b",
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