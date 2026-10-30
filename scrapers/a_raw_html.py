import json #json import, reads files into python
from bs4 import BeautifulSoup #brings in html parser, for searching
import requests #downloads webpages
from urllib.parse import urljoin, urlparse
import argparse
from urllib.robotparser import RobotFileParser

parser = argparse.ArgumentParser(description="Scraper (a): raw HTML")
parser.add_argument("--start-url", default="http://localhost:3000/") #default url to scrape, can be changed with command line argument
parser.add_argument("--page-cap", type=int, default=15) #max pages to scrape
parser.add_argument("--robots", choices=["obey", "ignore"], default="obey") #two choices obey and ignore
parser.add_argument("--run-id", required=True) # run id is required, tells the server whos asking
parser.add_argument("--out", required=True)# output file is required, where the scraped data will be saved
args = parser.parse_args()

labels = json.load(open("data/fields.json")) # opens file -> turns text into python data -> stores in variable

product_labels = []
for entry in labels["product"]:
    product_labels.append(entry["label"]) #adds the label to the list of product labels

#print(labels) #prints the data in the variable
# url = "http://localhost:3000/products/p1" #url of the page we want to scrape

# response = requests.get(url, headers = {"User-Agent":
#                                         "run=a-test-1"}, timeout = 5)
# # fetch the page, timout is 5 seconds, User-Agent tells the server whos asking

# soup = BeautifulSoup(response.content, "html.parser")
# #turns raw HTML into a tree of elements, then we are able to search through it

# for label in product_labels:
#     # Find the element with the label text
#     label_element = soup.find(string=label)
#     if label_element:
#         # Step to its parent element
#         parent_element = label_element.parent
#         # Step to the next element (the value)
#         value_element = parent_element.find_next_sibling()
#         if value_element:
#             print(f"{label}: {value_element.get_text(strip=True)}")
#         else:
#             print(f"{label}: Value not found")
#     else:
#         print(f"{label}: Label not found")

start_url = args.start_url
page_cap = args.page_cap
user_agent = f"run={args.run_id}" #user agent is the run id, tells the server whos asking

robots_url = urljoin(start_url, "/robots.txt")
robots_response = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=5)
rules = RobotFileParser()
rules.parse(robots_response.text.splitlines())

queue = [start_url] #list of urls to scrape
visited = set() #set of urls already scraped

while queue and len(visited) < page_cap:
    url = queue.pop(0) #get the first url in the queue
    if url in visited:
        continue
    visited.add(url)
    if args.robots == "obey" and not rules.can_fetch(user_agent, url):
        print("skipped (robots.txt):", url)
        continue
    response = requests.get(url, headers={"User-Agent": user_agent}, timeout=5) #fetch the page, timeout is 5 seconds, User-Agent tells the server whos asking
    print(response.status_code, url)

    soup = BeautifulSoup(response.content, "html.parser")
    for a in soup.find_all("a"):                 # every link, hidden ones too
        link = urljoin(url, a.get("href", ""))   
        same_site = urlparse(link).netloc == urlparse(start_url).netloc
        if same_site and link not in visited and link not in queue:
            queue.append(link)                   # wait in line to be visited

print(len(visited), "pages visited")

print("output will go to :", args.out)