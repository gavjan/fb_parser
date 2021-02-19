from __future__ import print_function

from bs4 import BeautifulSoup as soup  # HTML data structure
from urllib.request import Request, urlopen
from urllib.parse import quote
from json2xml import json2xml
import re
import os
import sys
import json
from async_get import async_get

# Enum states
DEL = 0
OK = 1
NEW = 2
UPDATE = 3


def load_json(name):
    data = {}
    try:
        f = open(f".json/{name}.json", "r")
        data = json.load(f)
        f.close()
    except FileNotFoundError:
        pass
    if "img_hash" not in data:
        data['img_hash'] = {}
    return data


def assert_folder(name):
    if not os.path.exists(name):
        os.mkdir(name)


def save_json(name, data):
    assert_folder(".json")
    f = open(f'.json/{name}.json', 'w')
    json.dump(data, f)
    f.close()


def err_exit(*args, **kwargs):
    print("[ERROR] ", end="", file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)
    print("\nPress Enter to exit...", file=sys.stderr)
    input()
    exit(1)


def print_json(_json, intend="", comma=False, left_bracket=True):
    if isinstance(_json, list):
        print(intend + "[")

        for i in range(len(_json)):
            print_json(_json[i], intend + "\t", comma=(i < len(_json) - 1))
        print(intend + "]")
        return

    def colored(color, text):
        return "\033[38;2;{};{};{}m{}\033[38;2;255;255;255m".format(color[0], color[1], color[2], text)

    green = [0, 255, 0]
    cyan = [0, 255, 255]
    if left_bracket:
        print(intend + "{")
    i = 0
    for key in _json:
        val = _json[key]
        if isinstance(_json[key], dict):
            print(f"{intend}\t{colored(green, key)}: {'{'}")
            print_json(_json[key], intend + "\t", left_bracket=False, comma=(i < len(_json) - 1))
        else:
            if isinstance(_json[key], str):
                val = f"\"{val}\"".replace("\n", "\\n")
            val_comma = "," if i < len(_json) - 1 else ""
            print(f"{intend}\t{colored(green, key)}: {colored(cyan, val)}{val_comma}")
        i += 1
    print(intend + "}" + ("," if comma else ""))


def load_html(file_name):
    if not os.path.exists("input") or not os.path.isfile("input/todo.html"):
        err_exit("input/todo.html missing")
    file = open(file_name)
    file_text = file.read()[11:]
    file_text = re.findall(r">todo</H3>[\s\S]*", file_text)
    if not file_text:
        err_exit("todo.html doesn't contain any product links.")
    file.close()
    return soup(file_text[0], "html.parser")


def load_page(url):
    def is_ascii(s):
        return all(ord(c) < 128 for c in s)

    if not is_ascii(url):
        for x in url:
            if not is_ascii(x):
                url = url.replace(x, quote(x))

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


def to_xml(db):
    xml = '<?xml version="1.0" encoding="utf-8"?><rss version="2.0" xmlns:g="http://base.google.com/ns/1.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
    xml_end = '</channel></rss>'
    for _id in db:
        if _id != "img_hash":
            xml += item_to_xml(db[_id])
    xml += xml_end
    return xml


def item_to_xml(_json):
    def arr_to_string(arr):
        return re.sub(r"['\[\]]", "", f"{arr}")

    copy = _json.copy()
    if "size" not in copy:
        print_json(copy)
    copy["size"] = arr_to_string(copy["size"])

    item_xml = json2xml.Json2xml(copy, attr_type=False).to_xml()
    item_xml = re.sub(r'(<\?xml version="1\.0" \?>|</?all>)\n', '', item_xml)
    item_xml = "\n<item>\n" + item_xml + "\n</item>\n"
    return item_xml


def parse_prod(job):
    page_url, html, prod = job['url'], job['data'], job['prod']

    print(page_url)
    page_soup = soup(html, "html.parser")
    prod_html = page_soup.find("div", {"class": "details-block"}).div.div.div

    prod["link"] = page_url

    prod["title"] = prod_html.find("li", {"class": "breadcrumb-item active"}).decode_contents()

    prod["id"] = prod_html.find("div", {"class": "product-id"}).decode_contents()
    prod["id"] = int(re.search(r"\d+", prod["id"]).group())

    brand = prod_html.find("div", {"class": "product-brnd-logo"}).img["src"]
    brand = re.search(r"[a-zA-Z-&]+\.(svg|png|jpg)", brand)
    if brand:
        brand = brand.group()
        prod["brand"] = re.search(r"[a-zA-Z-&]+", brand).group().replace("-", " ")
    else:
        prod["brand"] = ""

    price_block = prod_html.find("span", {"class": "old"})
    prod["price"] = price_block.decode_contents() if price_block else "0"
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

    # prod_sizes = []
    # for size in prod_html.find("select", {"id": "prodSizeChangeSel"}).find_all("option"):
    #     prod_sizes.append(size.decode_contents())
    # prod_sizes.sort()
    # prod["size"] = prod_sizes


def load_links_from_todo():
    prod_links = []
    all_prods = load_html("input/todo.html")
    all_prods = all_prods.find("dl")
    all_prods = all_prods.find_all("dt")
    for x in all_prods:
        prod_links.append(x.a["href"])
    return prod_links


def process_prods(db):
    jobs = []
    for prod_id in list(db):
        if prod_id != "img_hash":
            if db[prod_id]['state'] == DEL:
                del db[prod_id]
            elif db[prod_id]['state'] != OK:
                jobs.append({
                    'url': db[prod_id]['link'],
                    'prod': db[prod_id]
                })

    async_get(jobs, parse_prod)
    # parse_prod(db[prod_id]['link'], db[prod_id])


def scrape_sizes(link):
    page = load_page(link)
    page = page.find("div", {"class": "row"})
    page = page.find("div", {"class": "collapse"})
    sizes_raw = page.find_all("span", {"class": "tag"})

    tag_str = sizes_raw[0]["data-search-type"]
    tag = int(re.search(r"\d+", tag_str)[0])

    sizes = []
    for size in sizes_raw:
        sizes.append(size["data-search-value"])

    return sizes, tag


def link_to_hash(link):
    link = link.replace("https://topsale.am/img/prodpic/small/", "")
    return re.sub(r"\.(jpg|jpeg|png|webp|jfif)", "", link)


def new_product(db, img_hash, prod_link, prod_id):
    db['img_hash'][img_hash] = prod_id
    db[prod_id] = {
        "id": prod_id,
        "link": prod_link,
        "title": "",
        "brand": "",
        "size": [],
        "description": "",
        "price": "0 AMD",
        "sale_price": "0 AMD",
        "image_link": "",
        "additional_image_link": "",
        "google_product_category": 1604,  # Clothing by default
        "availability": "in stock",  # in stock by default
        "condition": "New",  # New condition by default
        "img_hash": img_hash,
        "state": NEW
    }


def arrays_are_equal(arr1, arr2):
    arr1.sort()
    arr2.sort()
    return arr1 == arr2


def exec_size(db, job, size=None, comma=False):
    def add_size(sizes, _prod_id, _size):
        if _prod_id not in sizes:
            sizes[_prod_id] = []
        if _size not in sizes[_prod_id]:
            sizes[_prod_id].append(_size)

    print(f"{size if size is not None else ''}{', ' if comma else ''}", end="")
    link = job['link']
    if size is not None:
        link = f"{link}?search=filters&searchData_TAG_{job['tag']}={size.replace(' ', '%20')}"

    page = load_page(link)
    page = page.find("div", {"class": "row"})
    list_items = page.find_all("div", {"class": "listitem"})

    scraped_sizes = job['scraped_sizes']
    for list_item in list_items:
        img_link = list_item.find("img", {"class": "img-1"})["data-src"]
        img_hash = link_to_hash(img_link)
        prod_link = list_item.find("a", {"class": "prod-item-img"})['href']
        prod_link = re.sub(r"[\n\r]", "", prod_link)
        prod_id = re.search(r"/\d+/", prod_link)[0].replace("/", "")

        parent_id = prod_id if img_hash not in db['img_hash'] else db['img_hash'][img_hash]
        add_size(scraped_sizes, parent_id, size)
        if img_hash not in db['img_hash']:
            new_product(db, img_hash, prod_link, prod_id)
        elif db[db['img_hash'][img_hash]]['state'] != NEW:
            parent_id = db['img_hash'][img_hash]

            if arrays_are_equal(scraped_sizes[parent_id], db[parent_id]['size']):
                db[parent_id]['state'] = OK
            else:
                db[parent_id]['state'] = UPDATE


def exec_sub_cat(db, job):
    print("\t", job['sub_category'], end=": ")

    no_size = ["Pens", "Ժամացույցներ", "Դրամապանակներ", "Արեւային ակնոցներ"]
    if job['sub_category'] in no_size:
        exec_size(db, job)
    else:
        sizes, job["tag"] = scrape_sizes(job["link"])
        i = 0
        for size in sizes:
            exec_size(db, job, size, comma=i < len(sizes) - 1)
            i += 1
    print("")


def update_with_website(db):
    for prod_id in db:
        if prod_id != "img_hash":
            db[prod_id]['state'] = DEL

    home = load_page("https://topsale.am/")

    categories = home.find("div", {"class": "categorylist"}).ul
    categories = categories.find_all("li", {"class": ["swiper-slide", "item menu-element"]})[:-1]

    # TODO: DELETE ME
    # categories = categories[2:3]

    scraped_sizes = {}
    for cat in categories:
        main_cat_name = cat.a.decode_contents().strip()
        sub_cats = cat.div.ul.find_all("li", {})

        print(main_cat_name)
        for sub_cat in sub_cats:
            job = {
                "main_category": main_cat_name,
                "sub_category": sub_cat.a.decode_contents().strip(),
                "link": sub_cat.a["href"],
                "scraped_sizes": scraped_sizes
            }
            job['sub_cat_id'] = int(re.search(r"\d+/$", job['link']).group()[:-1])

            exec_sub_cat(db, job)

    print_json(scraped_sizes)
    for prod_id in scraped_sizes:
        db[prod_id]['size'] = scraped_sizes[prod_id]


def main():
    db = load_json("db")

    update_with_website(db)
    process_prods(db)

    save_json("db", db)
    save_xml(to_xml(db))


main()
