# IPProxy

## 说明
项目目的解决在使用scrapy爬取数据时,不可避免碰到的使用代理IP问题.
网上也有比较好的项目,也可以直接拿来用. [qiyeboy/IPProxyPool](https://github.com/qiyeboy/IPProxyPool/)
之所以重复造轮子也是有原因的,也大体了解了qiyeboy的项目.
    1. 如果某段时间内迟迟达不到设定的最小值时,会导致多次重复抓取,IPProxyPool项目中没有IP的判重.如果抓取到相同的IP,如果再去判定有一定资源的消耗.
    2. 数据返回根据评分返回,如果评分过高的话,每次返回的ip都差不多,如果爬取速度过快怕被封ip.这个没测试,猜测.选取时,通过speed和score两个筛选数据的.
    3. 个别网站会被封.有几次xici代理直接封了ip可能跟那段时间重启程序有关.
    4. 自己有投机想法,直接在配置文件中配置目标网站.结果到后面目标网站把代理IP全封了.这个跟目标网站的反爬虫设置有关.为什么这么设置呢?因为项目返回的ip有时不能访问将爬取的网站.会出现失败.而scrapy自己又没有做太多处理,所以想提高代理Ip的有效性.

根据自己想法和实际情况,做了几点实现.主要为了保证代理ip的有效性.
    1. 增加BloomFilter,作为抓取ip判重,减少判定使用资源.这里使用的是基于redis的版本.大材小用吧.
    2. 使用redis作为数据存储和缓存.
    3. 探测目标爬取网站时,增加cookie机制.目前主要有随机ua,代理IP,带cookie访问.cookie解析成字符串存放redis.
    4. 通过Web方式公布api. http://0.0.0.0:1129/proxy/api/2 
    5. 代理通过轮询的方式给出.

TODO
    1. 增加启动停止脚本.
    2. 增加下限值判定.


## 安装
python 2.7版本
需要安装的软件:redis,lxml,gevent,redis-py等.

### 安装redis
ubuntu系统可以直接运行:apt-get install redis-server

### 安装python扩展包
使用pip install命令安装redis lxml gevent mmh3等.

## 使用


