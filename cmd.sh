#! /bin/bash

if [ $# != 1 ];then
    echo "usage cmd.sh start|stop|restart"
    exit
fi

function start () {
    setsid python main.py > /dev/null 2>&1 &
    return
}

function stop() { 
    ps -ef |grep ipproxy.py |awk '{print $2}'|xargs kill -9
    return 
}

function restart() { 
    stop
    start
    return
}

if [ $1 == "start" ];then
    start
elif [ $1 == "stop" ];then
    stop
elif [ $1 == "restart" ];then
    restart
fi
