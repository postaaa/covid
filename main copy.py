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

def extract_addressesEx(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    texts = re.findall(r'分别居住于：', content, re.MULTILINE)
    addresses = list(filter(lambda x: x!="", texts))
    return list(set(addresses))

def extract_addressesEx1(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    pattern = re.compile(r'>(.*?)<')
    x = pattern.findall(content)
    contenttmp =''
    contenttmp = contenttmp.join(x)
    texts = []
    texts1 = re.findall(r'居住于(\S+?)。', contenttmp, re.MULTILINE)
    texts2 = re.findall(r'居住于，(\S+?)。', contenttmp, re.MULTILINE)

    texts1.extend(texts2)    

    for singletexts in texts1:
        # texts = re.findall(r'\，(\S+?)，|。', contenttmp , re.MULTILINE)
        singletexts = singletexts.strip('：&nbsp;')
        singletexts = singletexts.strip('&nbsp;')
        textstmp = singletexts.split(r'，、')
        texts.extend(textstmp)
    # texts = re.findall(r'(.*?)', contenttmp ,re.S|re.M)
    addresses = list(filter(None, texts))
    return list(set(addresses))

def extract_addressesExFROMSTRING(str):
    str = ''
    texts = re.findall(r'\<span style\="font\-size\:16px\;font\-family\:宋体\">(\S+?)，\</span\>', str, re.MULTILINE)
    addresses = list(filter(lambda x: x!="", texts))
    return list(set(addresses))

def get_addresses():
    main_urls = ["https://wsjkw.sh.gov.cn/xwfb/index.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_2.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_3.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_4.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_5.html"
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
            m = re.match(r'上海2022年(\d+)月(\d+)日', title)
            if not m:
                m = re.match(r'3月19日（0-24时）本市各区确诊病例、无症状感染者居住地信息', title)
                if not m:                    
                    m = re.match(r'(\d+)月(\d+)日\（0-24时\）本市各区确诊病例', title)
                    if not m:   
                        continue
                    mon = int(m.group(1))
                    date = int(m.group(2))
                    dt = datetime.date(2022, mon, date)
                    dt_begin = datetime.date(2022, 3, 10)
                    if dt < dt_begin:
                        continue
                    url = base_url + sub_url
                    parts = extract_addressesEx1(url)
                    addresses.extend(parts);
                    continue
                mon = 3
                date = 19
                dt = datetime.date(2022, mon, date)
                dt_begin = datetime.date(2022, 3, 10)
                if dt < dt_begin:
                    continue
                url = base_url + sub_url
                parts = extract_addressesEx1(url)
                addresses.extend(parts);
                continue
            mon = int(m.group(1))
            date = int(m.group(2))
            dt = datetime.date(2022, mon, date)
            dt_begin = datetime.date(2022, 3, 10)
            if dt < dt_begin:
                continue
            url = base_url + sub_url
            parts = extract_addresses(url)
            addresses.extend(parts);  
    addresses = list(set(addresses))
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(addresses=addresses)
    with open("covid-map.html", "w",encoding='utf-8') as f:
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
                m = re.match(r'感染者居住地信息', title)
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
