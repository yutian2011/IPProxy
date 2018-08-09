# -*- coding: utf-8 -*-
from queue import Queue
from  lxml import etree
import requests
import random
from settings import *
import time
import socket
from pybloom_live import BloomFilter
from settings import log
import os
from settings import REFRESH_BF
from settings import MIN_NUM
import redis
import threading
import traceback

bloom = BloomFilter(capacity=100000, error_rate=0.001)

def get_pages(url):
    try:
        headers["User-Agent"] = random.choice(USER_AGENT_LIST)
        r = requests.get(url,headers=headers)
        if r.ok:
            return r.content
        else:
            return None
    except Exception as e:
        log.error("PID:%d error:%s url:%s" % (os.getpid(),traceback.format_exc(),url))
    return None

def parse_page(url, page, pattern):
    page = etree.HTML(page.lower()) 
    #page = etree.HTML(page.lower().decode('utf-8')) 
    ips = page.xpath(pattern["ip"])
    ports = page.xpath(pattern["port"])
    ty = page.xpath(pattern["type"])
    if ips == None or ports == None or ty == None:
        raise ValueError("current page "+str(ips)+str(ports)+str(ty))
    for i in range(len(ips)):
        ret = {}
        str = "%s:%s"
        ret["ip_port"] = str%(ips[i].text,ports[i].text)
        print(url, ret["ip_port"], ty[i].text)
        if ty[i].text.find("https") == -1:
            ret["type"] = 0
        else:
            ret["type"] = 1
        ret["db_flag"] = False
        yield ret

def get_and_check(url,pattern,q):
    try:
        page = get_pages(url)
        if page == None:
            return
        lists = parse_page(url, page, pattern)
        for ele in lists:
            is_existed = ele["ip_port"] in bloom
            #log.debug("PID:%d proxy worker ip %s  is_existed %d" % (os.getpid(),ele["ip_port"],is_existed))
            if is_existed == False:
                try:
                    bloom.add(ele["ip_port"])
                except Exception as e:
                    log.error("PID:%d bloom filter error:%s ip:%s" % (os.getpid(),e,ele["ip_port"]))
                q.put(ele)
    except Exception as e:
        log.error("PID:%d parse page error %s " % (os.getpid(), traceback.format_exc()))

def worker(pattern,q):
    try:
        num = pattern["page_range"]
        for i in range(len(pattern["url"])):
            index = pattern["url"][i].find("%d")
            log.debug("PID:%d url:%s" % (os.getpid(), str(pattern)))
            if index == -1:
                get_and_check(pattern["url"][i],pattern,q)
                time.sleep(10)
                continue
            for j in range(1,num+1):
                url = pattern["url"][i] % j
                get_and_check(url,pattern,q)
                time.sleep(10)
    except Exception as e:
        log.error("PID:%d proxy url error:%s %s " % (os.getpid(),traceback.format_exc(), str(pattern)))

def db_zcount():
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP, decode_responses=True)
    return r.zcard(REDIS_SORT_SET_COUNTS)

def get_proxy(q):
    #bloom.clear_all()
    times = 0
    while True:
        try:
            num = db_zcount()
            log.debug("PID:%d db current ips %d------" % (os.getpid(),num))
            while num > MIN_NUM:
                time.sleep(REFRESH_WEB_SITE_TIMEER)
                times += 1
                if times == REFRESH_BF:
                    bloom.clear()
                    times = 0
                    log.debug("PID:%d refresh bloom filter" % os.getpid())
            t1 = time.time()
            threads = []
            for key,value in list(URL_PATTERN.items()):
               thread = threading.Thread(target=worker,args=(value,q))
               thread.start()
               threads.append(thread)
            for thread in threads:
                thread.join()
            t2 = time.time()
            t = REFRESH_WEB_SITE_TIMEER - (t2 - t1)
            times += 1
            if t > 0:
                time.sleep(t)
                log.debug("PID:%d proxy sleep end------" % os.getpid())
                if times == REFRESH_BF:
                    bloom.clear()
                    times = 0
                    log.debug("PID:%d refresh bloom filter" % os.getpid())
        except Exception as e:
            log.error("PID:%d proxy error:%s" % (os.getpid(), traceback.format_exc()))
                

        

if __name__ == "__main__":
    q = Queue()
    get_proxy(q)
    #worker(URL_PATTERN[URL_LIST[0]],q)
            
