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
import os
import json


def main():
    ip_queue = multiprocessing.Queue()
    msg_queue = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=get_proxy,args=(ip_queue,msg_queue))
    p2 = multiprocessing.Process(target=test_and_verify.verify_db_data,args=(ip_queue,msg_queue))
    p3 = multiprocessing.Process(target=test_and_verify.gevent_queue,args=(ip_queue,msg_queue))
    p1.start()
    p2.start()
    p3.start()
    pid_list = [os.getpid(),p1.pid,p2.pid,p3.pid]
    with open(PID,"w") as f:
        f.write(json.dumps(pid_list))
    p1.join()
    p2.join()
    p3.join()


def test():
    test_and_verify.verify_ip_in_db()


if __name__ == '__main__':
    log.info("--------------------end-start--------------------------")
    main()
    #test()