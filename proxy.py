# -*- coding: utf-8 -*-
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
from settings import log
import os
from settings import REFRESH_BF

#bloom = BloomFilter(capacity=100000, error_rate=0.001)
bloom = pydrbloomfilter(100000, 0.001, REDIS_CONNECTION)

def get_pages(url):
    try:
        headers["User-Agent"] = random.choice(USER_AGENT_LIST)
        r = requests.get(url,headers=headers)
        if r.ok:
            return r.content
        else:
            return None
    except Exception as e:
        log.error("PID:%d error:%s url:%s" % (os.getpid(),e.message,url))
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
            log.debug("PID:%d url:%s" % (os.getpid(),url))
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
                        log.error("PID:%d bloom filter error:%s ip:%s" % (os.getpid(),e.message),ele["ip"])
                    q.put(ele)
                #print "element:",ele,is_existed
            #time.sleep(10)这里使用time的话,会导致线程sleep
            gevent.sleep(10)


def get_proxy(q,msg_queue):
    bloom.clear()
    times = 0
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
            log.debug("PID:%d web site sleep end" % os.getpid())
            if times == REFRESH_BF:
                bloom.clear()
                times = 0
                log.debug("PID:%d refresh bloom filter" % os.getpid())
            else:
                times += 1

        

if __name__ == "__main__":
    q = Queue()
    get_proxy(q)
    #worker(URL_PATTERN[URL_LIST[0]],q)
            
