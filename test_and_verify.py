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
from settings import DEST_URL
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
import os
from settings import log
from settings import TEST_PROCESS_NUM

def db_insert(ip_port,type,time,r=None):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    if r.zscore(REDIS_SORT_SET_TIME,ip_port) == None:
        r.zadd(REDIS_SORT_SET_COUNTS,0,ip_port)
    r.zadd(REDIS_SORT_SET_TIME,time,ip_port)
    r.zadd(REDIS_SORT_SET_TYPES,type,ip_port)

def db_insert_dest(name,ip_port,type,time,r=None):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    if r.zscore(name+":counts",ip_port) == None:
        r.zadd(name+":counts",0,ip_port)
    r.zadd(name+":time",time,ip_port)
    r.zadd(name+":types",type,ip_port)



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
    log.debug("PID:%d delete IP:%s " % (os.getpid(),ip))
    r.zrem(REDIS_SORT_SET_COUNTS,ip)
    r.zrem(REDIS_SORT_SET_TIME,ip)
    r.zrem(REDIS_SORT_SET_TYPES,ip)
    if STORE_COOKIE:
        r.delete(ip)
    db_delete_dest(ip,r)

# for all dest 
def db_delete_dest(ip,r):
    if r == None:
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    log.debug("PID:%d delete dest proxy IP:%s " % (os.getpid(),ip))
    for i in range(len(DEST_URL)):
        r.zrem(DEST_URL[i]["name"]+":counts",ip)
        r.zrem(DEST_URL[i]["name"]+":types",ip)
        r.zrem(DEST_URL[i]["name"]+":time",ip)
        if DEST_URL[i]["store_cookies"]:
            r.delete(DEST_URL[i]["name"]+":ip")




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

def test_dest_url(ip,is_http,dest_infos,redis=None):
    name = dest_infos["name"]
    url = dest_infos["url"]
    store_cookies = dest_infos["store_cookies"]
    use_default_cookies = dest_infos["use_default_cookies"]
    pro = {TYPES[is_http]:ip}
    time = 0
    flag= False
    try:
        r = None
        cookie_old = None
        r_cookies_key = "%s:%s" % (name,ip)
        if store_cookies and redis != None:
            cookie_old = redis.get(r_cookies_key)
            #print "old cookie:",cookie
            if cookie_old != None and cookie_old != "None" and cookie_old != "{}":
                #print "use cookie"
                log.debug("PID:%d IP:%s use old cookies:%s " % (os.getpid(),ip,cookie_old))
                cookies = cookiejar_from_dict(json.loads(cookie_old))
                r = requests.get(url,proxies=pro,cookies=cookies,timeout=SOKCET_TIMEOUT)
            else:
                if use_default_cookies:
                    rand_cookies = dest_infos["default_cookies"]
                    log.debug("PID:%d IP:%s use random cookies:%s " % (os.getpid(),ip,str(rand_cookies)))
                    cookie = cookiejar_from_dict(rand_cookies)
                    r = requests.get(url,proxies=pro,cookies=cookie,timeout=SOKCET_TIMEOUT)
                else:
                    r = requests.get(url,proxies=pro,timeout=SOKCET_TIMEOUT)
        else:
            if use_default_cookies:
                cookie = cookiejar_from_dict(dest_infos["default_cookies"])
                r = requests.get(url,proxies=pro,cookies=cookie,timeout=SOKCET_TIMEOUT)
            else:
                r = requests.get(url,proxies=pro,timeout=SOKCET_TIMEOUT)
        time += r.elapsed.microseconds/1000
        log.debug("PID:%d dest url:%s proxy ip:%s result:%d time:%d type:%s" % (os.getpid(),url,ip,r.status_code,time,TYPES[is_http]))
        if r.ok:
            flag = True
            if store_cookies and redis != None:
                #print "new cookies:",r.cookies
                if r.cookies != None :
                    cookie = json.dumps(dict_from_cookiejar(r.cookies))
                    if cookie and cookie != "{}" and cookie_old != cookie:
                        log.debug("PID:%d IP:%s new cookies:%s old cookies:%s" % (os.getpid(),ip,cookie,cookie_old))
                        redis.set(r_cookies_key,cookie)
    except Exception as e:
        log.debug("PID:%d error:%s" % (os.getpid(),e.message))
    return flag,time

def test_url(ip,is_http,redis=None):
    pro = {TYPES[is_http]:ip}
    #if redis == None:
    #    redis = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    time = 0
    flag= False
    try:
            #print "test url:",i,ip,pro
        r = None
        cookie_old = None
        if STORE_COOKIE and redis != None:
            cookie_old = redis.get(ip)
            #print "old cookie:",cookie
            if cookie_old != None and cookie_old != "None" and cookie_old != "{}":
                #print "use cookie"
                log.debug("PID:%d IP:%s use old cookies:%s " % (os.getpid(),ip,cookie_old))
                cookies = cookiejar_from_dict(json.loads(cookie_old))
                r = requests.get(TEST_URL,proxies=pro,cookies=cookies,timeout=SOKCET_TIMEOUT)
            else:
                if USE_DEFAULT_COOKIE:
                    rand_cookies = {"bid":random_str()}
                    log.debug("PID:%d IP:%s use random cookies:%s " % (os.getpid(),ip,str(rand_cookies)))
                    cookie = cookiejar_from_dict(rand_cookies)
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
        log.debug("PID:%d Test IP:%s result:%d time:%d type:%s" % (os.getpid(),ip,r.status_code,time,TYPES[is_http]))
        if r.ok:
            flag = True
            if STORE_COOKIE and redis != None:
                #print "new cookies:",r.cookies
                if r.cookies != None :
                    cookie = json.dumps(dict_from_cookiejar(r.cookies))
                    if cookie and cookie != "{}" and cookie_old != cookie:
                        log.debug("PID:%d IP:%s new cookies:%s old cookies:%s" % (os.getpid(),ip,cookie,cookie_old))
                        redis.set(ip,cookie)
    except Exception as e:
        log.debug("PID:%d error:%s" % (os.getpid(),e.message))
    return flag,time



def verify_ip_in_queues(q):
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    while True:
        try:
            item = q.get(timeout=QUEUE_TIMEOUT)
            log.debug("PID:%d verify_ip_in_queues dict infos:%s" % (os.getpid(),json.dumps(item)))
            #print "ip test:",item
            ret,time = test_url(item["ip_port"],item["type"],r)
            #log.debug("PID:%d queue ip:%s result:%d"%(os.getpid(),item["ip"],ret))
            if ret:
                if item.has_key("dest_cache"):
                    r.sadd(item["dest_cache"],item["ip_port"])
                else:
                    db_insert(item["ip_port"],item["type"],time,r)
                # if check db data,need not to check DEST_URL list
                if item["db_flag"]:
                    continue
                # test dest url
                for i in range(len(DEST_URL)):
                    flag,time = test_dest_url(item["ip_port"],item["type"],DEST_URL[i],r)
                    if flag:
                        db_insert_dest(DEST_URL[i]["name"],item["ip_port"],item["type"],time,r)
            else:
                if item["db_flag"]:
                    log.debug("PID:%d queue ip delete:%s"%(os.getpid(),item["ip_port"]))
                    db_delete(item["ip_port"],r)
        except Exception as e:
            log.error("PID:%d queue error:%s" % (os.getpid(),e.message))
            break
    return
    
def gevent_queue(q,msg_queue):
    while True:
        msg = msg_queue.get(block=True)
        log.debug("PID:%d gevent queue start---------------------->" % os.getpid())
        if TEST_PROCESS_NUM > 1 and msg == "OK":
            for i in range(TEST_PROCESS_NUM-1):
                msg_queue.put(os.getpid())
                log.debug("PID:%d gevent queue call other processes----" % os.getpid())
        glist = []
        for i in range(GEVENT_NUM):
            glist.append(gevent.spawn(verify_ip_in_queues,q))
        gevent.joinall(glist)
        l = msg_queue.qsize()
        for i in range(l):
            msg_queue.get()
        log.debug("PID:%d gevent queue end<----------------------" % os.getpid())

def get_ips_from_db(q):
    try:
        log.debug("PID:%d get_ips_from_db start---------------------->" % os.getpid())
        r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
        ips = db_select()
        i = 0
        for ip,type in ips:
            q.put({"ip_port":ip,"type":type,"db_flag":True})
            i += 1
        log.debug("PID:%d get_ips_from_db cur ip num:%d" % (os.getpid(),i))
    except Exception as e:
        log.error("PID:%d get_ips_from_db error:%s" % (os.getpid(),e.message))
    log.debug("PID:%d get_ips_from_db end<----------------------" % os.getpid())
    return



def verify_db_data(q,msg_queue):
    while True:
        msg_queue.put("OK")
        get_ips_from_db(q)
        time.sleep(REFRESH_DB_TIMER)

'''   
def verify_process(q,msg_queue):
    #p = multiprocessing.Process(target=gevent_db)
    #p.daemon = True
    #p.start()
    t = REFRESH_DB_TIMER
    while True:
        try:
            flag = 1
            start = time.time()
            msg_queue.get(timeout=t)
            log.debug("PID:%d queue start --- 659'e--->" % (os.getpid()))
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
'''



    
    