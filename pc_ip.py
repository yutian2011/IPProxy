# -*- coding = utf-8 -*-
import requests
import json
import redis
from settings import log
from settings import REDIS_SERVER
from settings import REDIS_PORT
from settings import DB_FOR_IP
import os
import time
from settings import WHOAMI

def get_local_ip():
    try:
        req = requests.get(WHOAMI)
        if req.ok:
            ip = req.text
            r = redis.StrictRedis(REDIS_SERVER, REDIS_PORT, DB_FOR_IP)
            ips = r.lrange("local_ip", 0, -1)
            if ip not in ips:
                r.lpush("local_ip", ip)
            num = r.llen("local_ip")
            if num > 2:
                r.brpop("local_ip")
        else:
            log.error("PID %d get_local_ip error url %s " % (os.getpid(), WHOAMI))
    except Exception as e:
        log.error("PID %d get_local_ip error %s " % (os.getpid(), str(e)))

def main():
    while True:
        get_local_ip()
        time.sleep(10)

