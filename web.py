# -*- coding: utf-8 -*-
import flask
import redis
from flask import Flask,jsonify
from settings import REDIS_PORT
from settings import REDIS_SERVER
from settings import REDIS_SORT_SET_COUNTS
from settings import REDIS_SORT_SET_TYPES
from settings import DB_FOR_IP
from settings import WEB_USE_REDIS_CACHE
from settings import STORE_COOKIE
from settings import REDIS_SET_CACHE

app = Flask(__name__)

TYPE = {0:"http",1:"https"}
def db_find(num):
    ret = []
    if num < 0:
        return None
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    ips = []
    n = 0
    cache_num = 0
    if WEB_USE_REDIS_CACHE:
        tmp = num
        cache_num = r.scard(REDIS_SET_CACHE)
        if cache_num < num:
            n = num - cache_num
            tmp = cache_num
        for i in range(tmp):
            ips.append(r.spop(REDIS_SET_CACHE))
    else:
        ips = r.zrange(REDIS_SORT_SET_COUNTS,0,num-1)
    if len(ips) == 0 and n == 0:
        return None
    if n > 0:
        ips.extend(r.zrange(REDIS_SORT_SET_COUNTS,0,n-1))
    for ip in ips:
        d = {}
        d["ip"] = ip
        if STORE_COOKIE:
            cookies = r.get(ip)
            if cookies != None:
                d["cookies"] = cookies
            else:
                d["cookies"] = ""
        if not WEB_USE_REDIS_CACHE:
            r.zincrby(REDIS_SORT_SET_COUNTS,ip)
        type = r.zscore(REDIS_SORT_SET_TYPES,ip)
        if type != None:
            d["type"] = TYPE[int(type)]
        else:
            continue
        ret.append(d)
    if n > 0:
        l = len(ips)
        i = cache_num
        while i < l:
            r.zincrby(REDIS_SORT_SET_COUNTS,ips[i])
            i += 1
    return ret

@app.route('/proxy/api/<int:num>', methods=['GET'])
def get_proxy(num):
    ret = db_find(num)
    if ret == None:
        return jsonify({"ret":False})
    else:
        return jsonify({"ret":True,"len":len(ret),"infos":ret})

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=1129,debug=True)