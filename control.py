#! /usr/bin/python
#　-*- coding: utf-8 -*-
import os
import sys
import signal
import commands
import json

def kill(pid):
    try:
        a = os.kill(pid, signal.SIGKILL)
    except OSError, e:
        print 'no process: %d' % pid

def stop():
    try:
        with open("./PROXY_PID","r") as f:
            line = f.readline()
            l = json.loads(line)
            for i in l:
                kill(i)
    except Exception as e:
        print "Stop Error:",e

def start():
    commands.getstatus("setsid python main.py")

def restart():
    stop()
    start()

def main():
    print len(sys.argv)
    if len(sys.argv) != 2:
        print "usage python control.py start|stop|restart"
        return None
    if d.has_key(sys.argv[1]):
        d[sys.argv[1]]()
    else:
        return None

d = {"start":start,"stop":stop,"restart":restart}
if __name__ == '__main__':
    main()
