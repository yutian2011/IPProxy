# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 10:40:49 2016

@author: KIDC
"""

from Queue import Queue
from  lxml import etree
import requests
import random
from settings import *
import gevent
import time
from gevent import monkey
from pybloom import BloomFilter
import socket
monkey.patch_socket()
from pydrbloomfilter.pydrbloomfilter import pydrbloomfilter

#bloom = BloomFilter(capacity=100000, error_rate=0.001)
bloom = pydrbloomfilter(100000, 0.001, REDIS_CONNECTION)

def get_pages(url):
    headers["User-Agent"] = random.choice(USER_AGENT_LIST)
    r = requests.get(url,headers=headers)
    if r.ok:
        return r.content
    else:
        return None

def parse_page(page,pattern):
    page = etree.HTML(page.lower()) 
    #page = etree.HTML(page.lower().decode('utf-8')) 
    ips = page.xpath(pattern["ip"])
    ports = page.xpath(pattern["port"])
    ty = page.xpath(pattern["type"])
    for i in range(len(ips)):
        ret = {}
        str = "%s:%s"
        ret["ip"] = str%(ips[i].text,ports[i].text)
        if ty[i].text.find("https") == -1:
            ret["type"] = 0
        else:
            ret["type"] = 1
        yield ret


def worker(pattern,q):
    num = pattern["page_range"]
    for i in range(len(pattern["url"])):
        for j in range(1,num+1):
            url = pattern["url"][i] % j
            print url
            page = get_pages(url)
            if page == None:
                continue
            lists = parse_page(page,pattern)
            for ele in lists:
                is_existed = ele["ip"] in bloom
                #print ele,is_existed
                if is_existed == False:
                    try:
                        bloom.add(ele["ip"])
                    except Exception as e:
                        print e
                    q.put(ele)
                #print "element:",ele,is_existed
            #time.sleep(10)这里使用time的话,会导致线程sleep
            gevent.sleep(10)


def get_proxy(q,msg_queue):
    bloom.clear()
    while True:
        msg_queue.put("OK")
        t1 = time.time()
        event = []
        for i in range(len(URL_LIST)):
           event.append(gevent.spawn(worker,URL_PATTERN[URL_LIST[i]],q))
        gevent.joinall(event)
        t2 = time.time()
        t = REFRESH_WEB_SITE_TIMEER - (t2 - t1)
        if t > 0:
            time.sleep(t)
            print "web site sleep end"
        

if __name__ == "__main__":
    q = Queue()
    get_proxy(q)
    #worker(URL_PATTERN[URL_LIST[0]],q)
            

#1.proxy gevent
#2.代理的生成. scrapy从数据库 中数据
#最后尝试开线程每个website,开协程在每一个网站+使用代理的方式
#webapi的形式         