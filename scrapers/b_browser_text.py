import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
#all three imports needed for this scraper so that it can scrap after js load

labels = json.load(open("data/fields.json")) #opening fields json file to get the labels for the fields we want to scrape
all_fields = labels["product"] + labels["article"] #setting all_fields to be both product and article from json

url = "http://127.0.0.1:3000/products/p1" #url we get to scrape
with sync_playwright() as p:
    browser = p.chromium.launch() #launching chromium browser
    page = browser.new_page(user_agent="run=b-test-1") #puts b-test-1 into each request, so we can identify each request
    response = page.goto(url, wait_until="load", timeout=5000) #waits until page as finish loading then goes on, give up after 5 sec if page is not loaded withing 5 sec
    print(response.status, url) #printing status of response and the url for confirmation
    soup = BeautifulSoup(page.content(), "html.parser") ##gets the page's html as the browser has it right after loading (after scripts ran), beautifulsoup turns it into a searchable tree
    browser.close() #close browser after scraping to not having it keep running

for field in all_fields: #iteration of all fields 
    label_element = soup.find(string=field["label"]) #find all fields with labels in json
    if label_element:
        value_element = label_element.parent.find_next_sibling() #.parent steps up to the label's element and .find... stesp to the element after it, which has the value
        if value_element:
            print(f"{field['label']}: {value_element.get_text(strip=True)}") #finds the text of the value