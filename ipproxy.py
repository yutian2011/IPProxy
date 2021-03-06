# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 09:56:44 2016

@author: KIDC
"""

import multiprocessing
import settings
import test_and_verify
from proxy import get_proxy
from settings import log
from settings import PID
from settings import WEB_USE_REDIS_CACHE
import os
import json
from webcache import web_cache_run
import pc_ip


def main():
    ip_queue = multiprocessing.Queue()
    #msg_queue = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=get_proxy, args=(ip_queue,))
    p2 = multiprocessing.Process(target=test_and_verify.verify_db_data, args=(ip_queue,))
    p3 = [multiprocessing.Process(target=test_and_verify.thread_queue, args=(ip_queue,)) for i in range(settings.TEST_PROCESS_NUM)]
    p4 = multiprocessing.Process(target=web_cache_run,args=(ip_queue,))
    p5 = multiprocessing.Process(target=pc_ip.main)
    p1.start()
    p2.start()
    for p in p3:
        p.start()
    if WEB_USE_REDIS_CACHE:
        p4.start()
    p5.start()
    #with open(PID,"w") as f:
    #    f.write(json.dumps(pid_list))
    p1.join()
    p2.join()
    for p in p3:
        p.join()
    if WEB_USE_REDIS_CACHE:
        p4.join()
    p5.join()

def test():
    test_and_verify.verify_ip_in_db()


if __name__ == '__main__':
    log.info("--------------------end-start--------------------------")
    main()
    #test()
