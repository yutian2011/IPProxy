# -*- coding: utf-8 -*-
import requests
import sys
import os
import time
from settings import TEST_URL
from settings import SOCKET_TIMEOUT
from settings import WORKER_NUM
from settings import REFRESH_DB_TIMER
from settings import DB_FOR_IP
from settings import REDIS_SERVER
from settings import REDIS_PORT
from settings import TYPES
from settings import QUEUE_TIMEOUT
from settings import STORE_COOKIE
from settings import USE_DEFAULT_COOKIE
from settings import DEST_URL
from settings import WHO
import requests
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict
from random import Random
import multiprocessing
import queue as InQueue
from multiprocessing import Queue
from queue import Empty
import json
import redis
import os
from settings import log
from settings import TEST_PROCESS_NUM
import threading
import traceback
import operator
from  lxml import etree
import math
import random
from requests.exceptions import ProxyError

def db_insert(ip_port, type, time, r, key):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER, REDIS_PORT, DB_FOR_IP, decode_responses=True)
    if r.zscore(key+":counts", ip_port) == None:
        r.zadd(key+":counts", 0, ip_port)
    r.zadd(key+":times", time, ip_port)
    r.zadd(key+":types",type,ip_port)

def db_select(r, key):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP, decode_responses=True)
    s = r.zrange(key+":counts",0,-1)
    if len(s) == 0:
        return 
    for i in s:
        type = (r.zscore(key+":types",i))
        if type == None:
            type = 0
        else:
            type = int(type)
        yield i,type

def db_delete(r, ip, key, cookie):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP, decode_responses=True)
    log.debug("PID:%d delete IP:%s key:%s" % (os.getpid(), ip, key))
    r.zrem(key+":counts", ip)
    r.zrem(key+":times", ip)
    r.zrem(key+":types", ip)
    if cookie != None:
        r.delete(cookie)

def db_find_one(key):
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP, decode_responses=True)
    s = r.zrange(key+":counts", 0, 0)
    if len(s) == 0:
        return None
    else:
        r.zincrby(key+":counts", s[0])
        return s[0]

def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str


class Anony():
    def __init__(self, url):
        self.url = url

    def get(self, ip, is_http, r):
        pass

class XXORG(Anony):
    def get(self, ip, is_http, r):
        try:
            pro = {TYPES[is_http]:ip}
            req = requests.get(self.url, proxies=pro, timeout=SOCKET_TIMEOUT)
            pip = ip.split(":")[0]
            if req.ok:
                page = req.text
                page = etree.HTML(page)
                eles = page.xpath("//div[@id='result']/text()")
                #print(eles, len(eles))#['\r\n\t\tREMOTE_ADDR:\t103.75.117.249', 'HTTP_VIA:\t', 'HTTP_X_FORWARDED_FOR:\t', '\t'] 4

                if len(eles) == 6:
                    return 1
                elif len(eles) == 5:
                    return 1
                elif len(eles) < 4:
                    return 0
                else:
                    remote = eles[0].replace("\t", "").split(":")[1]
                    forward = eles[2].replace("\t", "").split(":")[1]
                    pc = r.lrange("local_ip", 0, -1)
                    log.info("PID:%d WHO xxorg proxy ip:%s remote:%s forward:%s  cur pc:%s" % (os.getpid(), ip, remote, forward, str(pc)))
                    if remote in pc:
                        return -1
                    if len(forward) == 0:
                        return 2
                    else:
                        return 1
            else:
                return 0
        except Exception as e:
            log.error("PID:%d WHO xxorg ip:%s error:%s" % (os.getpid(), ip, e))
            return 0 


class Cmem(Anony):
    def get(self, ip, is_http, r):
        try:
            pro = {TYPES[is_http]:ip}
            req = requests.get(self.url, proxies=pro, timeout=SOCKET_TIMEOUT)
            pip = ip.split(":")[0]
            if req.ok:
                ips = req.text
                ips = ips.strip("\n")
                ips = ips.split(" ")
                #print(WHO, ips)
                if len(ips) == 2:
                    return 1
                pc = r.lrange("local_ip", 0, -1)
                if ips[0] in pc:
                    return -1
                else:
                    return 2
            return 0
        except Exception as e:
            log.error("PID:%d C3322 ip:%s error:%s" % (os.getpid(), ip, e))
            return 0

xxorg = XXORG(WHO["xxorg"])
cmem = Cmem(WHO["3322"])
check_objs = [xxorg, cmem]
def check_proxy_anonymity(ip, is_http, r):
    for obj in check_objs:
        ret = obj.get(ip, is_http, r)
        if ret != 0:
            return ret
    return 0


def test_url(name, url, ip, is_http, store_cookies, use_default_cookies, check_anonymity, redis):
    pro = {TYPES[is_http]:ip}
    #pro = {"http": ip, "https": ip}
    t = 0
    flag= False
    anonymity = 0
    try:
        cookie_key = "%s:%s" % (name, ip)
        req = None
        cookie_old = None
        if store_cookies and redis != None:
            cookie_old = redis.get(cookie_key)
            if cookie_old != None and cookie_old != "None" and cookie_old != "{}":
                log.debug("PID:%d IP:%s use old cookies:%s " % (os.getpid(), ip, cookie_old))
                cookies = cookiejar_from_dict(json.loads(cookie_old))
                req = requests.get(url, proxies=pro, cookies=cookies, timeout=SOCKET_TIMEOUT)
            else:
                if use_default_cookies:
                    rand_cookies = {"bid":random_str()}
                    log.debug("PID:%d IP:%s use random cookies:%s " % (os.getpid(),ip,str(rand_cookies)))
                    cookie = cookiejar_from_dict(rand_cookies)
                    req = requests.get(url, proxies=pro, cookies=cookie, timeout=SOCKET_TIMEOUT)
                else:
                    req = requests.get(url, proxies=pro, timeout=SOCKET_TIMEOUT)
        else:
            if use_default_cookies:
                cookie = cookiejar_from_dict({"bid":random_str()})
                req = requests.get(url, proxies=pro, cookies=cookie, timeout=SOCKET_TIMEOUT)
            else:
                req = requests.get(url, proxies=pro, timeout=SOCKET_TIMEOUT)
        t = req.elapsed.microseconds / 1000
        log.debug("PID:%d Test url %s ip:%s result:%d time:%d type:%s" % (os.getpid(), url, ip, req.status_code, t, TYPES[is_http]))
        if req.ok:
            flag = True
            if store_cookies and redis != None:
                if req.cookies != None :
                    cookie = json.dumps(dict_from_cookiejar(req.cookies))
                    log.debug("PID:%d IP:%s new cookies:%s old cookies:%s" % (os.getpid(),ip,cookie,cookie_old))
                    if cookie and cookie != "{}" and not operator.eq(cookie_old, cookie):
                        log.debug("PID:%d IP:%s new cookies:%s old cookies:%s" % (os.getpid(),ip,cookie,cookie_old))
                        redis.set(cookie_key, cookie)
            if check_anonymity:
                time.sleep(10)
                anonymity = check_proxy_anonymity(ip, is_http, redis)
    except Exception as e:
        #traceback.print_exc()
        log.debug("PID:%d test url error:%s" % (os.getpid(),e))
    return flag, t, anonymity

def verify_ip_in_queues(q):
    ts = time.time()
    ts = math.modf(ts)
    random.seed(ts[0]*1000000)
    while True:
        try:
            r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP, decode_responses=True)
            item = q.get(block=True)
            log.debug("PID:%d verify_ip_in_queues dict infos:%s" % (os.getpid(),item))
            time.sleep(random.uniform(5, 20))
            times = 0 #name, url, ip, is_http, store_cookies, use_default_cookies, check_anonymity, redis=None
            ret, t, anonymity = test_url(item["name"], item["url"], item["ip_port"], item["type"], item["store_cookies"], item["use_default_cookies"], item["check_anonymity"], r)
            db_key = None
            if item["db"] == 0:
                db_key = "proxy"
            elif item["db"] == 1:
                db_key = item["name"]
            elif item["db"] == 2:
                db_key = item["name"]+":webcache"
            if ret:
                log.info("PID:%d verify_ip_in_queues %s anonymity ret:%d" % (os.getpid(),item["ip_port"], anonymity))
                if anonymity == -1:
                    continue
                if item["db"] == 0:
                    #db_insert(item["ip_port"], item["type"], time, r, db_key)
                    for i in DEST_URL:
                        info = {}
                        info["name"] = i["name"]
                        info["url"] = i["url"]
                        info["ip_port"] = item["ip_port"]
                        info["type"] = item["type"]
                        info["store_cookies"] = i["store_cookies"]
                        info["use_default_cookies"] = i["use_default_cookies"]
                        info["db"] = 1
                        info["check_anonymity"] = False
                        q.put(info)
                db_insert(item["ip_port"], item["type"], t, r, db_key)
            else:
                log.debug("PID:%d queue ip delete:%s %d"%(os.getpid(), item["ip_port"], item["db"]))
                if item["db"] == 1:
                    db_delete(r, item["ip_port"], db_key, "%s:%s"%(item["name"], item["ip_port"]))
                elif item["db"] == 2:
                    db_delete(r, item["ip_port"], db_key, None)
                    db_delete(r, item["ip_port"], item["name"], "%s:%s"%(item["name"], item["ip_port"]))
                else:
                    db_delete(r, item["ip_port"], db_key, None)
            #times += 1
        except redis.exceptions.ConnectionError as e:
            log.error("PID:%d queue error:%s" % (os.getpid(),e))
            time.sleep(60)
        except Exception as e:
            log.error("PID:%d queue error:%s" % (os.getpid(),traceback.format_exc()))
            #break
    return

def thread_queue(q):
    while True:
        try:
            threads = []
            for i in range(WORKER_NUM):
                thread = threading.Thread(target=verify_ip_in_queues, args=(q,))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
        except Exception as e:
            pass

def get_ips_from_db(q):
    try:
        log.debug("PID:%d get_ips_from_db start---------------------->" % os.getpid())
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP, decode_responses=True)
        ips = db_select(r, "global")
        i = 0
        for ip,type in ips:#url, ip, is_http, store_cookies, use_default_cookies, check_anonymity, redis=None
            q.put({"name":"global", "url":TEST_URL, "ip_port":ip, "type":type, "store_cookies":STORE_COOKIE, "use_default_cookies":USE_DEFAULT_COOKIE, "check_anonymity":True, "db":0})
            i += 1
        log.debug("PID:%d get_ips_from_db cur ip num:%d" % (os.getpid(),i))
    except Exception as e:
        log.error("PID:%d get_ips_from_db error:%s" % (os.getpid(),traceback.format_exc()))
    log.debug("PID:%d get_ips_from_db end<----------------------" % os.getpid())
    return



def verify_db_data(q):
    while True:
        get_ips_from_db(q)
        time.sleep(REFRESH_DB_TIMER)


    
    
