import json #json import, reads files into python
from bs4 import BeautifulSoup #brings in html parser, for searching
import requests #downloads webpages
from urllib.parse import urljoin, urlparse

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

start_url = "http://localhost:3000/" #starting url
page_cap = 15
queue = [start_url] #list of urls to scrape
visited = set() #set of urls already scraped

while queue and len(visited) < page_cap:
    url = queue.pop(0) #get the first url in the queue
    if url in visited:
        continue
    visited.add(url)
    response = requests.get(url, headers={"User-Agent": "run=a-test-1"}, timeout=5) #fetch the page, timeout is 5 seconds, User-Agent tells the server whos asking
    print(response.status_code, url)

    soup = BeautifulSoup(response.content, "html.parser")
    for a in soup.find_all("a"):                 # every link, hidden ones too
        link = urljoin(url, a.get("href", ""))   
        same_site = urlparse(link).netloc == urlparse(start_url).netloc
        if same_site and link not in visited and link not in queue:
            queue.append(link)                   # wait in line to be visited

print(len(visited), "pages visited")
        
