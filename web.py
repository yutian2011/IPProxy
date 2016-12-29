# -*- coding: utf-8 -*-
import flask
import redis
from flask import Flask,jsonify
from settings import REDIS_PORT
from settings import REDIS_SERVER
from settings import REDIS_SORT_SET_COUNTS
from settings import REDIS_SORT_SET_TYPES
from settings import DB_FOR_IP

app = Flask(__name__)


def db_find_one(num,cookie=False):
    if num < 0:
        return None
    r = redis.StrictRedis(REDIS_SERVER,REDIS_PORT,DB_FOR_IP)
    s = r.zrange(REDIS_SORT_SET_COUNTS,0,num-1)
    cookies = []
    if len(s) == 0:
        return None
    else:
        for i in range(num):
            r.zincrby(REDIS_SORT_SET_COUNTS,s[i])
            if cookie == True:
                cookies.append(r.get(s[i]))
        return s,cookies

@app.route('/proxy/api/<int:num>', methods=['GET'])
def get_proxy(num):
    ret,cookies = db_find_one(num)
    if ret == None:
        return jsonify({"ret":False})
    else:
        return jsonify({"ret":True,"proxy":ret})

@app.route('/proxy/api/cookies/<int:num>', methods=['GET'])
def get_proxy_with_cookies(num):
    ret,cookies = db_find_one(num,True)
    if ret == None:
        return jsonify({"ret":False})
    else:
        return jsonify({"ret":True,"proxy":ret,"cookies":cookies})

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=1129,debug=True)