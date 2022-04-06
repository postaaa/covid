import argparse
from copyreg import add_extension
import json
import datetime
import re
from jinja2 import Environment, FileSystemLoader
import requests
from lxml import etree
import os

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"}

def extract_addresses(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    texts = re.findall(r'居住于(\S+?)，|。', content, re.MULTILINE)    
    addresses = list(filter(lambda x: x!="", texts))
    return list(set(addresses))

""" def extract_addressesEx(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    texts = re.findall(r'分别居住于：', content, re.MULTILINE)
    addresses = list(filter(lambda x: x!="", texts))
    return list(set(addresses)) """


def extract_addressesEx(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    pattern = re.compile(r'>(.*?)<')
    x = pattern.findall(content)
    contenttmp =''
    contenttmp = contenttmp.join(x)
    texts = []
    textsQuName = re.findall(r'日，(\S+?)区' , contenttmp, re.MULTILINE)
     
    texts1 = re.findall(r'居住于(\S+?)。', contenttmp, re.MULTILINE)
    texts2 = re.findall(r'居住于，(\S+?)。', contenttmp, re.MULTILINE)

    texts1.extend(texts2)    

    for singletexts in texts1:
        # texts = re.findall(r'\，(\S+?)，|。', contenttmp , re.MULTILINE)
        singletexts = singletexts.strip('：&nbsp;')
        singletexts = singletexts.strip('&nbsp;')
        singletexts = singletexts.strip('，&nbsp;')
        singletexts = re.sub(r"[\u4e00-\u9fa5]+区", "", singletexts)
        textstmp = re.split(r'[，；、\s]',singletexts)
        
        # textstmp = singletexts.split(r'[，；、\s]')
        texts.extend(textstmp)
    # texts = re.findall(r'(.*?)', contenttmp ,re.S|re.M)
    addresses = list(filter(None, texts))
    return list(set(addresses))

def extract_addressesEx1(url):
    r = requests.get(url, headers=headers, verify=False)
    content = r.content.decode("utf-8")
    pattern = re.compile(r'>(.*?)<')
    x = pattern.findall(content)
    contenttmp =''
    contenttmp = contenttmp.join(x)
    texts = []
    textsQuName = re.findall(r'日，(\S+?)区' , contenttmp, re.MULTILINE)
     
    contenttmp = re.sub(r" ", "&nbsp;", contenttmp)   
    texts1 = re.findall(r'居住于(\S+?)。', contenttmp, re.MULTILINE)
    i=0
    for singletexts in texts1:
        # texts = re.findall(r'\，(\S+?)，|。', contenttmp , re.MULTILINE)
        singletexts = singletexts.strip('：&nbsp;')
        singletexts = singletexts.strip('&nbsp;')
        singletexts = singletexts.strip('，&nbsp;')
        textstmp = re.split(r'[，；、\s]',singletexts)
        # textstmp = singletexts.split(r'[，；、\s]')
        #textsend = [textsQuName[i]+ "区" +str(textstmp[j]) for j in range(len(textstmp))]
        texts.extend(textstmp)        
        i = i+1 
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
        "https://wsjkw.sh.gov.cn/xwfb/index_5.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_6.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_7.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_8.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_9.html",
        "https://wsjkw.sh.gov.cn/xwfb/index_10.html"
    ]
    base_url = "https://wsjkw.sh.gov.cn"
    addresses = []
    filename = ""
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
                # m = re.match(r'3月19日（0-24时）本市各区确诊病例、无症状感染者居住地信息', title)                
                m = re.match(r'(\d+)月(\d+)日\（0-24时\）本市各区确诊病例', title)                
                if not m:                    
                    m = re.match(r'【最新】(\d+)月(\d+)日\（0-24时\）本市各区确诊病例', title)
                    if not m:   
                        continue
                    mon = int(m.group(1))
                    date = int(m.group(2))
                    if len(filename) == 0:
                        if len(m.group(1)) == 1:
                            monstr = '0'+m.group(1)    
                        else:
                            monstr = m.group(1)                      
                        if len(m.group(2)) == 1:
                            datestr = '0'+m.group(2)
                        else:
                            datestr = m.group(2)     
                        filename = r'scr/covid-map-2022-'+ monstr +'-'+ datestr +'.html'
                    dt = datetime.date(2022, mon, date)
                    dt_begin = datetime.date(2022, 3, 10)
                    if dt < dt_begin:
                        continue
                    if str.startswith(sub_url,'https'):
                        url = sub_url
                    else:
                        url = base_url + sub_url
                    parts = extract_addressesEx1(url)
                    addresses.extend(parts);
                    continue
                mon = int(m.group(1))
                date = int(m.group(2))
                if len(filename) == 0:
                    if len(m.group(1)) == 1:
                        monstr = '0'+m.group(1)    
                    else:
                        monstr = m.group(1)                      
                    if len(m.group(2)) == 1:
                        datestr = '0'+m.group(2)
                    else:
                        datestr = m.group(2)     
                    filename = r'scr/covid-map-2022-'+ monstr +'-'+ datestr +'.html'
                dt = datetime.date(2022, mon, date)
                dt_begin = datetime.date(2022, 3, 10)
                if dt < dt_begin:
                    continue
                if str.startswith(sub_url,'https'):
                    url = sub_url
                else:
                    url = base_url + sub_url
                parts = extract_addressesEx1(url)
                addresses.extend(parts);
                continue
            mon = int(m.group(1))
            date = int(m.group(2))
            if len(filename) == 0:
                if len(m.group(1)) == 1:
                    monstr = '0'+m.group(1)    
                else:
                    monstr = m.group(1)                      
                if len(m.group(2)) == 1:
                    datestr = '0'+m.group(2)
                else:
                    datestr = m.group(2)     
                filename = r'scr/covid-map-2022-'+ monstr +'-'+ datestr +'.html'
            dt = datetime.date(2022, mon, date)
            dt_begin = datetime.date(2022, 3, 10)
            if dt < dt_begin:
                continue
            if str.startswith(sub_url,'https'):
                url = sub_url
            else:
                url = base_url + sub_url
            parts = extract_addresses(url)
            addresses.extend(parts);  
    addresses = list(set(addresses))
    addressesReslut = []
    countReslut = []
    for address in addresses:
        # address = address.strip()
        # address = re.sub(r"^[\u4e00-\u9fa5]+区", "", address)
        # if len(address) == 0:
        #     continue        
        if not address in addressesReslut:            
            addressesReslut.append(address)
            countReslut.append(1)
        else:
            i = addressesReslut.index(address)
            countReslut[i] += 1
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('map_template.html')
    output = template.render(addresses=addressesReslut,counts=countReslut)
    with open(filename, "w",encoding='utf-8') as f:
        f.write(output)
    
    out ="<html><head><meta charset='UTF-8'><title>Covid-Map</title></head><body>\n <br>\n All data comes from public information on the official website and is not responsible for any errors. All web pages are for testing purposes and circulation and commercial use are strictly prohibited. <br>\n<hr></hr>\n<ol>\n";
    out += WalkDir("scr")
    new_func(out)
    Save2File("scr/index.html",out)

def new_func(out):
    out +="\n</ol>\n<hr></hr>"



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

def Save2File(pathname,content):
    fw = open(pathname,"wt",encoding="utf-8")
    fw.write(content)
    fw.close()

def WalkDir(dirname):
    out =""
    try:
        ls=os.listdir(dirname)
    except:
        print ("Access Deny.")
    else:
        for fn in ls:
            temp=os.path.join(dirname,fn)
            if (os.path.isdir(temp)):
                out += "<h3>"+temp+"</h3>\n"
                out +="<ol>\n"
                
                out +=WalkDir(temp)
                out +="</ol>\n"
            else:                
                if re.match(r"covid-map-2022-", fn, flags=0):
                    out +="<li><a href=\""+fn+"\">"+fn+"</a></li>\n"
    return out

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
