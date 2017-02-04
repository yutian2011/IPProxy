# -*- coding: utf-8 -*-
import redis
import json
import time
import test_and_verify
from settings import log
#from test_and_verify import test_url
from settings import TYPES
from settings import GEVENT_NUM
from settings import REDIS_SET_CACHE
from settings import REDIS_SERVER
from settings import REDIS_PORT
from settings import DB_FOR_IP
from settings import REDIS_SORT_SET_TIME
from settings import REDIS_SORT_SET_COUNTS
from settings import REDIS_SORT_SET_TYPES
from settings import WEB_USE_REDIS_CACHE
from settings import WEB_CACHE_REFRESH
from settings import STORE_COOKIE
from settings import TEST_URL
from settings import SOKCET_TIMEOUT
from settings import CACHE_FOR_URL
from pybloom import BloomFilter
from settings import RETRY_TIMES
import os
import gevent
import requests

from gevent import monkey
monkey.patch_socket()

class CacheIPForDest(object):
    def __init__(self,p):
        self.p = p
        self.r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)

    def select_ip_for_check(self):
        f = BloomFilter(capacity=10000,error_rate=0.001)
        arr = []
        for i in CACHE_FOR_URL:
            data = self.r.smembers(i["name"]+":webcache")
            for ip in data:
                if ip in f:
                    continue
                else:
                    f.add(ip)
                d = {}
                d["ip_port"] = ip
                #log.debug("PID:%d web cache cache ip:%s" % (os.getpid(),ip))
                type = self.r.zscore(REDIS_SORT_SET_TYPES,ip)
                if type == None:#already delete
                    self.r.srem(i["name"]+":webcache",ip)
                    continue
                d["type"] = int(type)
                d["db_flag"] = True
                d["dest_cache"] = i["name"]+":webcache"
                #d["name"] = i
                self.p.put(d)
                #log.debug("PID:%d web cache dict infos:%s" % (os.getpid(),json.dumps(d)))
            cur_num = self.r.scard(i["name"]+":webcache")
            diff = i["num"] - cur_num
            log.debug("PID:%d web cache name:%s  cur:%d" % (os.getpid(),i["name"],diff))
            if diff < 0 :
                continue
            s = self.r.zrange(i["name"]+":counts",0,2*diff - 1)
            for ip in s:
                d = {}
                d["ip_port"] = ip
                #log.debug("PID:%d web cache pool ip:%s" % (os.getpid(),ip))
                type = self.r.zscore(REDIS_SORT_SET_TYPES,ip)
                if type == None:
                    continue
                d["type"] = int(type)
                d["db_flag"] = True
                d["dest_cache"] = i["name"]+":webcache"
                #d["name"] = i
                #log.debug("PID:%d web cache dict infos:%s" % (os.getpid(),json.dumps(d)))
                self.p.put(d)

    def run(self):
        try:
            while True:
                log.debug("PID:%d web cache start ---------------------------" % os.getpid())
                t1 = time.time()
                i = 0
                while i < RETRY_TIMES:
                    self.select_ip_for_check()
                    i += 1
                log.debug("PID:%d web cache end ---------------------------" % os.getpid())
                t2 = time.time()
                t = WEB_CACHE_REFRESH - ( t2 - t1 )
                if t > 0 :
                    time.sleep(t)
                log.debug("PID:%d web cache sleep end ---------------------------" % os.getpid())
        except Exception as e:
                log.error("PID:%d web cache error:%s " % (os.getpid(),e.message))


        

class WebCachedIP(object):
    def __init__(self):
        self.cur_num = 0
        self.cur_pos = 0
        self.len = 0

    def db_set_select(self,r,set_name,is_sort,num=-1):
        s = []
        if num > 0 and is_sort:
            num = num -1
        if is_sort:
            s = r.zrange(set_name,0,num)
        else:
            s = r.srandmember(set_name,num)
        if len(s) == 0:
            return 0,None
        return len(s),s

    def db_delete(self,r,ip,is_cached):
        log.debug("PID:%d web cache delete IP:%s " % (os.getpid(),ip))
        if is_cached:
            r.srem(REDIS_SET_CACHE,ip)
        '''
        r.zrem(REDIS_SORT_SET_COUNTS,ip)
        r.zrem(REDIS_SORT_SET_TIME,ip)
        r.zrem(REDIS_SORT_SET_TYPES,ip)
        if STORE_COOKIE:
            r.delete(ip)
        '''
    def test_url(self,ip,is_http,redis=None):
        pro = {TYPES[is_http]:ip}
        time = 0
        flag= False
        try:
            r = requests.get(TEST_URL,proxies=pro,timeout=SOKCET_TIMEOUT)
            log.debug("PID:%d Web cache ip:%s result:%d type:%s" % (os.getpid(),ip,r.status_code,TYPES[is_http]))
            if r.ok:
                flag = True
        except Exception as e:
            log.debug("PID:%d error:%s" % (os.getpid(),e.message))
        return flag


    def test_ip(self,r,ips,is_cached):
        if ips == None or r == None:
            return
        while True:
            #print "cur pos:",self.cur_pos,self.len,self.cur_num
            if self.cur_pos == self.len - 1 :
                #print "end"
                break
            #print ips,len(ips)
            ip = ips[self.cur_pos]
            self.cur_pos += 1
            type = r.zscore(REDIS_SORT_SET_TYPES,ip)
            ret = False
            if type != None:
                ret = self.test_url(ip,int(type))
            #log.debug("PID:%d web cache IP:%s  " % (os.getpid(),ip))
            if not ret:
                self.db_delete(r,ip,is_cached)
                self.cur_num -= 1
            elif not is_cached:
                r.zincrby(REDIS_SORT_SET_COUNTS,ip)
                r.sadd(REDIS_SET_CACHE,ip)
                self.cur_num += 1
                if self.cur_num > WEB_CACHE_IP_NUM:
                    break

    def web_ip_cache(self):
        while True:
            t1 = time.time()
            try:
                r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
                num,ips = self.db_set_select(r,REDIS_SET_CACHE,False,WEB_CACHE_IP_NUM)
                self.cur_num = num
                self.cur_pos = 0
                self.len = num
                #print ips
                #print "cur num",self.cur_num,self.cur_pos,self.len
                if num >0 and ips != None and len(ips) > 0 :
                    glist = [gevent.spawn(self.test_ip,r,ips,True) for i in range(GEVENT_NUM)]
                    gevent.joinall(glist)
                times = 0
                while self.cur_num < WEB_CACHE_IP_NUM and times < 1024:
                    #print "cur num",self.cur_num
                    n = (WEB_CACHE_IP_NUM - self.cur_num)*2
                    num,ips = self.db_set_select(r,REDIS_SORT_SET_COUNTS,True,n)
                    self.cur_pos = 0
                    self.len = num
                    times += 1
                    if num == 0 or ips == None:
                        continue
                    glist = [gevent.spawn(self.test_ip,r,ips,False) for i in range(GEVENT_NUM)]
                    gevent.joinall(glist)
                    #print "cur num end ",self.cur_num
            except Exception as e:
                #print e
                log.error("PID:%d web cache error:%s" % (os.getpid(),e))
            finally:
                t2 = time.time()
                #print "sleep"
                t = WEB_CACHE_REFRESH - ( t2 - t1 )
                if t > 0:
                    time.sleep(t)

def web_cache_run(p):
    #obj = WebCachedIP()
    #obj.web_ip_cache()
    obj = CacheIPForDest(p)
    obj.run()

if __name__ == "__main__":
    obj = WebCachedIP()
    obj.web_ip_cache()
