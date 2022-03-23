import argparse
import json
import datetime
import re
from jinja2 import Environment, FileSystemLoader
import requests
from lxml import etree


singletexts = "闵行区浦鸥路 , 浦叶路 , 闵行区浦连路, , 浦鸥路"

# texts = re.sub(r"[\u4e00-\u9fa5]+区", "", singletexts)

addressesReslut = []
countReslut = []
for address in singletexts:
    address = address.strip()
    address = re.sub(r"^[\u4e00-\u9fa5]+区", "", address)
    if len(address) == 0:
        continue        
    if not address in addressesReslut:            
        addressesReslut.append(address)
        countReslut.append(1)
    else:
        i = addressesReslut.index(address)
        countReslut[i] += 1

print (addressesReslut)

print (countReslut)