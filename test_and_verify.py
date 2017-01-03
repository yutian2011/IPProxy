# -*- coding: utf-8 -*-
import requests
import sys
import os
import time
from settings import TEST_URL
from settings import SOKCET_TIMEOUT
from settings import GEVENT_NUM
from settings import REFRESH_DB_TIMER
from settings import DB_FOR_IP
from settings import REDIS_SERVER
from settings import REDIS_PORT
from settings import REDIS_SORT_SET_TIME
from settings import REDIS_SORT_SET_COUNTS
from settings import REDIS_SORT_SET_TYPES
from settings import TYPES
from settings import QUEUE_TIMEOUT
from settings import STORE_COOKIE
from settings import USE_DEFAULT_COOKIE
import requests
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict
from random import Random
import gevent
import multiprocessing
import Queue as InQueue
from multiprocessing import Queue
from Queue import Empty
import json
from gevent import monkey
monkey.patch_socket()
monkey.patch_ssl()
import redis
from settings import log

def db_insert(ip_port,type,time,r=None):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    if r.zscore(REDIS_SORT_SET_TIME,ip_port) == None:
        r.zadd(REDIS_SORT_SET_COUNTS,0,ip_port)
    r.zadd(REDIS_SORT_SET_TIME,time,ip_port)
    r.zadd(REDIS_SORT_SET_TYPES,type,ip_port)



def db_select(r=None):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    s = r.zrange(REDIS_SORT_SET_COUNTS,0,-1)
    if len(s) == 0:
        return 
    for i in s:
        type = (r.zscore(REDIS_SORT_SET_TYPES,i))
        if type == None:
            type = 0
        else:
            type = int(type)
        yield i,type

def db_delete(ip,r):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    log.debug(r.zrem(REDIS_SORT_SET_COUNTS,ip))
    r.zrem(REDIS_SORT_SET_TIME,ip)
    r.zrem(REDIS_SORT_SET_TYPES,ip)
    if STORE_COOKIE:
        r.delete(ip)

def db_find_one():
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    s = r.zrange(REDIS_SORT_SET_COUNTS,0,0)
    if len(s) == 0:
        return None
    else:
        r.zincrby(REDIS_SORT_SET_COUNTS,s[0])
        return s[0]

def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

def test_url(ip,is_http,redis=None):
    pro = {TYPES[is_http]:ip}
    time = 0
    flag= False
    try:
            #print "test url:",i,ip,pro
        r = None
        cookie_old = None
        if STORE_COOKIE and redis != None:
            cookie = redis.get(ip)
            #print "old cookie:",cookie
            if cookie != None and cookie != "None" and cookie != "{}":
                #print "use cookie"
                cookie_old = cookiejar_from_dict(json.loads(cookie))
                r = requests.get(TEST_URL,proxies=pro,cookies=cookie_old,timeout=SOKCET_TIMEOUT)
            else:
                if USE_DEFAULT_COOKIE:
                    cookie = cookiejar_from_dict({"bid":random_str()})
                    r = requests.get(TEST_URL,proxies=pro,cookies=cookie,timeout=SOKCET_TIMEOUT)
                else:
                    r = requests.get(TEST_URL,proxies=pro,timeout=SOKCET_TIMEOUT)
        else:
            if USE_DEFAULT_COOKIE:
                cookie = cookiejar_from_dict({"bid":random_str()})
                r = requests.get(TEST_URL,proxies=pro,cookies=cookie,timeout=SOKCET_TIMEOUT)
            else:
                r = requests.get(TEST_URL,proxies=pro,timeout=SOKCET_TIMEOUT)
        time += r.elapsed.microseconds/1000
        log.debug("PID:%d Test IP:%s result:%d time:%d" % (os.getpid(),ip,r.status_code,time))
        if r.ok:
            flag = True
            if STORE_COOKIE:
                #print "new cookies:",r.cookies
                if r.cookies != None :
                    cookie = json.dumps(dict_from_cookiejar(r.cookies))
                    if cookie_old != cookie:
                        #print "store new cookie:",cookie
                        redis.set(ip,cookie)
    except Exception as e:
        log.debug("PID:%d error:%s" % (os.getpid(),e.message))
    return flag,time


def verify_ip_in_queues(q):
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    while True:
        try:
            item = q.get(timeout=QUEUE_TIMEOUT)
            #print "ip test:",item
            ret,time = test_url(item["ip"],item["type"],r)
            #log.debug("PID:%d queue ip:%s result:%d"%(os.getpid(),item["ip"],ret))
            if ret:
                db_insert(item["ip"],item["type"],time,r)
        except Exception as e:
            log.error("PID:%d queue error:%s" % (os.getpid(),e.message))
    return


def verify_ip_in_db(q,r):
    try:
        while True:
            msg = q.get(timeout=5)
            ip = msg["ip_port"]
            type = msg["type"]
            ret,time = test_url(ip,type,r)
            #log.debug("PID:%d redis ip:%s result:%d time:%d" % (os.getpid(),ip,ret,time))
            if ret == False:
                db_delete(ip,r)
            else:
                db_insert(ip,type,time,r)
    except Exception as e:
        log.error("PID:%d db error:%s" % (os.getpid(),e.message))
        
    
def gevent_queue(q):
    log.debug("PID:%d gevent queue start---------------------->" % os.getpid())
    glist = []
    for i in range(GEVENT_NUM):
        glist.append(gevent.spawn(verify_ip_in_queues,q))
    gevent.joinall(glist)
    log.debug("PID:%d gevent queue end<----------------------" % os.getpid())

def gevent_db():
    log.debug("PID:%d gevent db start---------------------->" % os.getpid())
    glist = []
    q = InQueue.Queue()
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    ips = db_select()
    for ip,type in ips:
        q.put({"ip_port":ip,"type":type})
    if q.empty():
        log.debug("PID:%d db no data" % os.getpid())
        log.debug("PID:%d gevent db end<----------------------" % os.getpid())
        return
    for i in range(GEVENT_NUM):
        glist.append(gevent.spawn(verify_ip_in_db,q,r))
    gevent.joinall(glist)
    log.debug("PID:%d gevent db end<----------------------" % os.getpid())
        
def verify_process(q,msg_queue):
    p = multiprocessing.Process(target=gevent_db)
    p.daemon = True
    p.start()
    t = REFRESH_DB_TIMER
    while True:
        try:
            flag = 1
            start = time.time()
            msg_queue.get(timeout=t)
            log.debug("PID:%d queue start ------>" % (os.getpid()))
            #verify_ip_in_queues(q)
            p = multiprocessing.Process(target=gevent_queue,args=(q,))
            p.daemon = True
            p.start()
            p.join()
        except (Empty) as e: #也可以通过with Timeout(10)方式
            log.debug("PID:%d db start ------>" % (os.getpid()))
            flag = 2
            #verify_ip_in_db()
            p = multiprocessing.Process(target=gevent_db)
            p.daemon = True
            p.start()
            p.join()
        finally:
            end = time.time()
            log.debug("PID:%d last sleep time:%f used:%f" % (os.getpid(),t,end - start))
            if flag == 1:
                if end - start >= t :
                    t1 = time.time()
                    p = multiprocessing.Process(target=gevent_db)
                    p.daemon = True
                    p.start()
                    p.join()
                    t2 = time.time()
                    t = REFRESH_DB_TIMER - (t2 - t1)
                    if t < 0:
                        t = REFRESH_DB_TIMER
                else:
                    t = t - (end - start)
            elif flag ==2:
                t = REFRESH_DB_TIMER





def test_verify_ip_in_queues(q):
    l = []
    for i in range(10):
        l.append(gevent.spawn(verify_ip_in_queues,q))
    gevent.joinall(l)
    
    