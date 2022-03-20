import time
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


def get_date_range():
    urls = get_urls()
    dates = []
    for url in urls:
        r = requests.get(url, headers=headers, verify=False)
        content = r.content.decode("utf-8")
        html = etree.HTML(content)
        title = html.xpath('//h1[@id="activity-name"]')[0].text
        m = re.search(r'(\d+)月(\d+)日', title)
        month = int(m.group(1))
        day = int(m.group(2))
        dt = datetime.date(year=2022, month=month, day=day)
        dates.append(dt)
    dates.sort()
    start = dates[0]
    end = dates[-1]
    result = "{}月{}日-{}月{}日".format(start.month, start.day, end.month, end.day)
    return result


def export_points():
    urls = get_urls()
    addresses = []
    for url in urls:
        r = requests.get(url, headers=headers, verify=False)
        content = r.content.decode("utf-8")
        html = etree.HTML(content)
        title = html.xpath('//h1[@id="activity-name"]')[0].text
        m = re.search(r'(\d+)月(\d+)日', title)
        month = int(m.group(1))
        day = int(m.group(2))
        if not m:
            raise Exception("date not found in title: {}".format(title))
        parts = extract_addresses(url)
        if len(parts) > 0:
            addresses.extend(parts);
        else:
            parts = get_agg_addresses(url)
            addresses.extend(parts)

    addresses = list(set(addresses))
    print(len(addresses))
    points = list(map(lambda x: get_address_point(x), addresses))
    points = list(filter(lambda x: x is not None, points))

    directory = os.path.dirname(__file__)
    filepath = os.path.join(directory, "points")
    with open(filepath, "w") as f:
        f.write(json.dumps(points))


def import_points():
    directory = os.path.dirname(__file__)
    filepath = os.path.join(directory, "points")
    f = None
    try:
        f = open(filepath)
        content = f.read()
        points = json.loads(content)
    except:
        return []
    finally:
        f.close()
    return points


def get_addresses():
    points = import_points()
    range_text = get_date_range()
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(points=points, range_text=range_text)
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
    texts = list(map(lambda x: re.sub(r'，|。|、', '', x), texts))
    texts = list(filter(lambda x: x != '', texts))
    return texts


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
    city_address = "上海市" + address
    url = "https://apis.map.qq.com/ws/geocoder/v1/?address={}&region={}&key={}".format(city_address, "上海", key)
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    resp = json.loads(content)
    if resp["status"] != 0:
        print("error getting point for {} due to {}".format(city_address, resp["message"]))
        return None
    lng = resp["result"]["location"]["lng"]
    lat = resp["result"]["location"]["lat"]
    time.sleep(0.5)
    return {"lng": lng, "lat": lat, "address": address}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=None, help="e.g. 2022-01-04")
    parser.add_argument("--url", type=str, default=None, help="e.g. https://")
    parser.add_argument("--urlagg", type=str, default=None, help="e.g. https://")
    parser.add_argument("--export", action="store_true", default=None, help="")
    args = parser.parse_args()
    if args.date:
        get_addresses_on_date(args.date)
    elif args.url:
        get_addresses_from_url(args.url)
    elif args.urlagg:
        get_agg_addresses_from_url(args.urlagg)
    elif args.export:
        export_points()
    else:
        get_addresses()
