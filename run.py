from __future__ import print_function

from bs4 import BeautifulSoup as soup  # HTML data structure
from urllib.request import Request, urlopen
from json2xml import json2xml
import re
import os
import sys


def err_exit(*args, **kwargs):
    print("[ERROR] ", end="", file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)
    print("\nPress Enter to exit...", file=sys.stderr)
    input()
    exit(1)


def load_html(file_name):
    if not os.path.exists("input") or not os.path.isfile("input/todo.html"):
        err_exit("input/todo.html missing")
    file = open(file_name)
    file_text = file.read()[11:]
    file_text = re.findall(r">todo</H3>[\s\S]*", file_text)[0]
    file.close()
    return soup(file_text, "html.parser")


def load_page(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_byte = urlopen(req).read()
    webpage = web_byte.decode('utf-8')
    page = soup(webpage, "html.parser")
    return page


def save_xml(xml_str):
    if not os.path.exists("output"):
        os.mkdir("output")
    xml_file = open("output/result.xml", "w", encoding="utf-8")
    xml_file.write(xml_str)
    xml_file.close()


def to_xml(json):
    item_xml = json2xml.Json2xml(json).to_xml()
    item_xml = re.sub(r'(<\?xml version="1\.0" \?>|</?all>)\n', '', item_xml)
    item_xml = "\n<item>\n" + item_xml + "\n</item>\n"
    return item_xml


def parse_prod(page_url):
    prod = {
        "id": 0,
        "link": "",
        "title": "",
        "brand": "",
        "size": "",
        "description": "",
        "price": "0 AMD",
        "sale_price": "0 AMD",
        "image_link": "",
        "additional_image_link": "",
        "google_product_category": 1604,  # Clothing by default
        "availability": "in stock",  # in stock by default
        "condition": "New",  # New condition by default

    }
    print(page_url)
    page_soup = load_page(page_url)
    prod_html = page_soup.find("div", {"class": "details-block"}).div.div.div

    prod["link"] = page_url

    prod["title"] = prod_html.find("li", {"class": "breadcrumb-item active"}).decode_contents()

    prod["id"] = prod_html.find("div", {"class": "product-id"}).decode_contents()
    prod["id"] = int(re.search(r"\d+", prod["id"]).group())

    prod["brand"] = prod_html.find("div", {"class": "product-brnd-logo"}).img["src"]
    prod["brand"] = re.search(r"[a-zA-Z-&]+\.(svg|png|jpg)", prod["brand"]).group()
    prod["brand"] = re.search(r"[a-zA-Z-&]+", prod["brand"]).group().replace("-", " ")

    prod["price"] = prod_html.find("span", {"class": "old"}).decode_contents()
    prod["price"] = re.search(r"[0-9,]+", prod["price"]).group().replace(",", "") + " AMD"

    prod["sale_price"] = prod_html.find("span", {"class": "regular"}).decode_contents()
    prod["sale_price"] = re.search(r"[0-9,]+", prod["sale_price"]).group().replace(",", "") + " AMD"

    prod["description"] = prod_html.find("div", {"class": "extra-description"}).decode_contents()

    prod["description"] = prod["description"].lower()
    prod["description"] = re.sub(r'(<li>|• )', '\n• ', prod["description"])
    prod["description"] = re.sub(r'\n<[^>]+>\n', '', prod["description"])
    prod["description"] = re.sub(r'<[^>]+>', '', prod["description"])

    pic_arr = prod_html.find_all("li", {"class": "slider-thumb"})
    prod_pics = []
    for pic in pic_arr:
        prod_pics.append(pic.img["src"])
    prod["image_link"] = prod_pics[0]

    for pic in prod_pics[1:-1]:
        prod["additional_image_link"] += pic + ",\n"
    prod["additional_image_link"] += prod_pics[-1]

    type_str = prod_html.find("ol", {"class": "breadcrumb"}).find_all("li")[2].a.decode_contents()
    prod["google_product_category"] = type_str

    prod_sizes = []
    for size in prod_html.find("select", {"id": "prodSizeChangeSel"}).find_all("option"):
        prod_sizes.append(size.decode_contents())
    prod["size"] = prod_sizes[0]
    for size in prod_sizes[1:]:
        prod["size"] += ", " + size

    return prod


type_map = {  # https://www.google.com/basepages/producttype/taxonomy-with-ids.en-US.txt
    "Կոշիկներ": 187,
    "Շապիկներ": 212,
    "Ջինսեր": 204,
    "Հողաթափեր": 187,
    "Սպորտային համազգեստ": 3598,
    "Բաճկոններ": 5598,
    "Լողազգեստ, ներքնազգեստ": 211,
    "Վերնաշապիկներ եւ սվիտերներ": 212,
    "Շապիկներ և պոլոներ": 212,
    "Զգեստներ": 2271,
    "Վերնաշապիկներ և բլուզներ": 212,
    "Հագուստ": 212,
    "Գոտիներ": 169,
    "Դրամապանակներ": 6551,

}
prod_links = []
xml = '<?xml version="1.0" encoding="utf-8"?><rss version="2.0" xmlns:g="http://base.google.com/ns/1.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
xml_end = '</channel></rss>'
all_prods = load_html("input/todo.html")
all_prods = all_prods.find("dl")
all_prods = all_prods.find_all("dt")
for x in all_prods:
    prod_links.append(x.a["href"])

for link in prod_links:
    prod_json = parse_prod(link)
    xml += to_xml(prod_json)

xml += xml_end
save_xml(xml)
