from bs4 import BeautifulSoup as soup  # HTML data structure
from urllib.request import Request, urlopen
from json2xml import json2xml
import re


def load_html(file_name):
    return soup(open(file_name), "html.parser")


def load_page(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_byte = urlopen(req).read()
    webpage = web_byte.decode('utf-8')
    page = soup(webpage, "html.parser")
    return page


prod = {
    "id": 0,
    "link": "",
    "type": "",
    "name": "",
    "brand": "",
    "size": "",
    "description": "",
    "price": 0,
    "old_price": 0,
    "pics": []
}
page_url = "https://topsale.am/product/karl-imagination-quote-tee/15057//"
page_soup = load_page(page_url)
prod_html = page_soup.find("div", {"class": "details-block"}).div.div.div

prod["name"] = prod_html.find("li", {"class": "breadcrumb-item active"}).decode_contents()

prod["id"] = prod_html.find("div", {"class": "product-id"}).decode_contents()
prod["id"] = int(re.search(r"\d+", prod["id"]).group())

prod["brand"] = prod_html.find("div", {"class": "product-brnd-logo"}).img["src"]
prod["brand"] = re.search(r"[a-zA-Z-&]+\.(svg|png|jpg)", prod["brand"]).group()
prod["brand"] = re.search(r"[a-zA-Z-&]+", prod["brand"]).group().replace("-", " ")

prod["price"] = prod_html.find("span", {"class": "regular"}).decode_contents()
prod["price"] = int(re.search(r"[0-9,]+", prod["price"]).group().replace(",", ""))

prod["old_price"] = prod_html.find("span", {"class": "old"}).decode_contents()
prod["old_price"] = int(re.search(r"[0-9,]+", prod["old_price"]).group().replace(",", ""))

prod["description"] = prod_html.find("div", {"class": "extra-description"}).p.decode_contents().replace("<br/>", "")

pic_arr = prod_html.find_all("li", {"class": "slider-thumb"})
prod["pics"] = []
for pic in pic_arr:
    prod["pics"].append(pic.img["src"])

prod["type"] = prod_html.find("ol", {"class": "breadcrumb"}).find_all("li")[2].a.decode_contents()

prod["size"] = prod_html.find("select", {"id": "prodSizeChangeSel"}).option.decode_contents()

print(prod)
