import os.path
import argparse
import json
import datetime
import re
from jinja2 import Environment, FileSystemLoader
import requests
from lxml import etree

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"}

def extract_addresses(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    texts = re.findall(r'居住于(\S+?)，|。', content, re.MULTILINE)
    addresses = list(filter(lambda x: x!="", texts))
    return list(set(addresses))


def get_urls():
    directory = os.path.dirname(__file__)
    filepath = os.path.join(directory, "urls")
    with open(filepath) as f:
        content = f.read()
        lines = content.split("\n")
        urls = list(filter(lambda x: x != "", lines))
    return urls


def get_addresses():
    urls = get_urls()
    addresses = []
    for url in urls:
        r = requests.get(url, headers=headers, verify=False)
        content = r.content.decode("utf-8")
        html = etree.HTML(content)
        title = html.xpath('//h1[@id="activity-name"]')[0].text
        print(title)
        m = re.search(r'(\d+)月(\d+)日', title)
        if not m:
            raise Exception("date not found in title: {}".format(title))
        parts = extract_addresses(url)
        if len(parts) > 0:
            addresses.extend(parts);
        else:
            parts = get_agg_addresses(url)
            addresses.extend(parts)

    addresses = list(set(addresses))
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(addresses=addresses)
    with open("covid-map.html", "w") as f:
        f.write(output)


def get_addresses_on_date(date):
    main_urls = ["https://wsjkw.sh.gov.cn/xwfb/index.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_2.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_3.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_4.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_5.html"
    ]
    base_url = "https://wsjkw.sh.gov.cn"
    addresses = []
    dt = datetime.datetime.strptime(date, "%Y-%m-%d")
    for main_url in main_urls:
        r = requests.get(main_url, headers=headers, verify=False)
        content = r.content.decode("utf-8")
        html = etree.HTML(content)
        a_nodes = html.xpath('//ul[contains(@class, "list-date")]/li/a')
        for node in a_nodes:
            sub_url = node.attrib["href"]
            title = node.attrib["title"]
            patt = '上海2022年{}月{}日'.format(dt.month, dt.day)
            m = re.match(patt, title)
            if not m:
                continue
            url = base_url + sub_url
            parts = extract_addresses(url)
            addresses.extend(parts);
    addresses = list(set(addresses))
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(addresses=addresses)
    filename = "covid-map-{}.html".format(date)
    with open(filename, "w") as f:
        f.write(output)


def get_addresses_from_url(url):
    addresses = extract_addresses(url)
    addresses = list(set(addresses))
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    html = etree.HTML(content)
    title = html.xpath('//h1[@id="activity-name"]/text()')[0]
    m = re.search(r'(\d+)月(\d+)日', title)
    mon = int(m.group(1))
    date = int(m.group(2))
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(addresses=addresses)
    filename = "covid-map-2022-{:02d}-{:02d}.html".format(mon, date)
    with open(filename, "w") as f:
        f.write(output)


def get_agg_addresses(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    html = etree.HTML(content)
    span_nodes = html.xpath('//section[@data-role="title"]//section[@data-autoskip="1"]/p/span')
    addresses = []
    texts = []
    for node in span_nodes:
        texts.append(node.text)
    texts = list(filter(lambda x: x is not None and not re.search(r'终末消毒', x), texts))
    texts = list(filter(lambda x: x != '无', texts))
    addresses = list(map(lambda x: re.sub(r'，|。|、', '', x), texts))
    return addresses


def get_agg_addresses_from_url(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    html = etree.HTML(content)
    span_nodes = html.xpath('//section[@data-role="title"]//section[@data-autoskip="1"]/p/span')
    addresses = []
    texts = []
    for node in span_nodes:
        texts.append(node.text)
    texts = list(filter(lambda x: x is not None and not re.search(r'终末消毒', x), texts))
    texts = list(filter(lambda x: x != '无', texts))
    addresses = list(map(lambda x: re.sub(r'，|。|、', '', x), texts))
    print(addresses)
    title = html.xpath('//h1[@id="activity-name"]/text()')[0]
    m = re.search(r'(\d+)月(\d+)日', title)
    mon = int(m.group(1))
    date = int(m.group(2))
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(addresses=addresses)
    filename = "covid-map-2022-{:02d}-{:02d}.html".format(mon, date)
    with open(filename, "w") as f:
        f.write(output)


def get_address_point(address):
    key = "ILZBZ-6UOEO-O27WF-SA3PG-OH2NS-FLF4Z"
    url = "https://apis.map.qq.com/ws/geocoder/v1/?address={}&region={}&key={}".format(address, "上海", key)
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    resp = json.loads(content)
    if resp["status"] != 0:
        raise Exception("error getting point for {}".format(address))
    lng = resp["result"]["location"]["lng"]
    lat = resp["result"]["location"]["lat"]
    return {"lng": lng, "lat": lat, "address": address}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=None, help="e.g. 2022-01-04")
    parser.add_argument("--url", type=str, default=None, help="e.g. https://")
    parser.add_argument("--urlagg", type=str, default=None, help="e.g. https://")
    args = parser.parse_args()
    if args.date:
        get_addresses_on_date(args.date)
    elif args.url:
        get_addresses_from_url(args.url)
    elif args.urlagg:
        get_agg_addresses_from_url(args.urlagg)
    else:
        get_addresses()
