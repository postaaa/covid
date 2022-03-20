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
    # texts = re.findall(r'居住于:(\S+?)，|。', content, re.MULTILINE)
    # texts = re.findall(r'(?<=居住于：).\S+?(?=。)', content, re.MULTILINE)
    # texts = re.findall(r'分别居住于：(\S+?)', content, re.MULTILINE)
    texts = re.findall(r'\<span style=\"font\-size\:16px\;font\-family\:宋体\">(\S+?)，\</span\>', content, re.MULTILINE)
    addresses = list(filter(lambda x: x!="", texts))
    return list(set(addresses))

def get_addresses():
    """ main_urls = ["https://wsjkw.sh.gov.cn/xwfb/index.html"
    ]
    base_url = "https://wsjkw.sh.gov.cn"
    addresses = []
    for main_url in main_urls:
        r = requests.get(main_url, headers=headers, verify=False)
        content = r.content.decode("utf-8")
        html = etree.HTML(content)
        a_nodes = html.xpath('//ul[contains(@class, "list-date")]/li/a')
        for node in a_nodes:
            sub_url = node.attrib["href"]
            title = node.attrib["title"]
      
            m = re.match(r'(\d+)月(\d+)日\（0-24时\）本市各区确诊病例', title)
            if not m:
                continue
            mon = int(m.group(1))
            date = int(m.group(2))
            dt = datetime.date(2022, mon, date)
            dt_begin = datetime.date(2022, 3, 10)
            if dt < dt_begin:
                continue
            url = base_url + sub_url """
    parts = extract_addresses('https://wsjkw.sh.gov.cn/xwfb/20220320/f9f1683cf055471fb1a67b8586e36660.html')
    addresses.extend(parts);
    addresses = list(set(addresses))


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
