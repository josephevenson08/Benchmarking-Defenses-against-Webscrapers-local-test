import requests

page_text = """Demo Shop
HomeProducts
Product details
Name
Larkfield Studio Headphones
Brand
Larkfield
Category
Headphones
Price
$89.99
SKU
LF-HP-2041
Rating
4.5
Reviews
1,284
Availability
In stock
Release date
2024-09-12
Description
Closed-back over-ear headphones with 40 mm drivers and a detachable cable.
Synthetic test site for a local scraping study. All content is made up."""

question = "What is the SKU and rating?"

reply = requests.post(
    "http://127.0.0.1:11434/api/generate",
    json={
        "model": "llama3.2:3b",
        "prompt": page_text + "\n\n" + question,
        "stream": False,
        "options": {"temperature": 0},
    },
    timeout=120,
)
data = reply.json()
print(data["response"])
print("seconds:", round(data["total_duration"] / 1e9, 2))