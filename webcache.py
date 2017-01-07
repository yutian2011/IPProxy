# -*- coding: utf-8 -*-
import redis
import json
import time
import test_and_verify
from settings import log
from test_and_verify import test_url
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
from settings import WEB_CACHE_IP_NUM
from settings import WEB_CACHE_REFRESH
from settings import STORE_COOKIE

import gevent
from gevent import monkey
monkey.patch_socket()

'''
#---redis---------------------------------------
REDIS_SERVER = "127.0.0.1"
REDIS_PORT = 6379
DB_FOR_IP = 0
REDIS_SORT_SET_TIME = "proxy_time"
REDIS_SORT_SET_COUNTS = "proxy_counts"
REDIS_SORT_SET_TYPES = "proxy_types"
#---web cache----------------------------------
WEB_USE_REDIS_CACHE = True
WEB_CACHE_IP_NUM = 60
WEB_CACHE_REFRESH = 3*60
REDIS_SORT_SET_CACHE = "web_cache"
'''

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
        if is_cached:
            r.srem(REDIS_SET_CACHE,ip)
        r.zrem(REDIS_SORT_SET_COUNTS,ip)
        r.zrem(REDIS_SORT_SET_TIME,ip)
        r.zrem(REDIS_SORT_SET_TYPES,ip)
        if STORE_COOKIE:
            r.delete(ip)

    def test_ip(self,r,ips,is_cached):
        if ips == None or r == None:
            return
        while True:
            #print "cur pos:",self.cur_pos,self.len,self.cur_num
            if self.cur_pos == self.len - 1 :
                #print "end"
                break
            print ips,len(ips)
            ip = ips[self.cur_pos]
            self.cur_pos += 1
            type = r.zscore(REDIS_SORT_SET_TYPES,ip)
            ret = False
            time = 0
            if type != None:
                ret,time = test_url(ip,int(type))
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
                print ips
                #print "cur num",self.cur_num,self.cur_pos,self.len
                if num >0 and ips != None and len(ips) > 0 :
                    glist = [gevent.spawn(self.test_ip,r,ips,True) for i in range(GEVENT_NUM)]
                    gevent.joinall(glist)
                times = 0
                while self.cur_num < WEB_CACHE_IP_NUM and times < 1024:
                    print "cur num",self.cur_num
                    n = (WEB_CACHE_IP_NUM - self.cur_num)*2
                    num,ips = self.db_set_select(r,REDIS_SORT_SET_COUNTS,True,n)
                    self.cur_pos = 0
                    self.len = num
                    glist = [gevent.spawn(self.test_ip,r,ips,False) for i in range(GEVENT_NUM)]
                    gevent.joinall(glist)
                    times += 1
                    #print "cur num end ",self.cur_num
            except Exception as e:
                print e
                #log.error("PID:%d web cache error:%s" % (os.getpid(),e))
            finally:
                t2 = time.time()
                #print "sleep"
                t = WEB_CACHE_REFRESH - ( t2 - t1 )
                if t > 0:
                    time.sleep(t)

def web_cache_run():
    obj = WebCachedIP()
    obj.web_ip_cache()

if __name__ == "__main__":
    obj = WebCachedIP()
    obj.web_ip_cache()
