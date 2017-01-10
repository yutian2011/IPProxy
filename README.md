# IPProxy

## 说明
  项目目的解决在使用scrapy爬取数据时,不可避免碰到的使用代理IP问题. 

  网上也有比较好的项目,也可以直接拿来用.  [qiyeboy/IPProxyPool](https://github.com/qiyeboy/IPProxyPool/) 
  之所以重复造轮子也是有原因的,也大体了解了qiyeboy的项目. 

1. 如果某段时间内迟迟达不到设定的最小值时,会导致多次重复抓取,IPProxyPool项目中没有IP的判重.如果抓取到相同的IP,如果再去判定有一定资源的消耗. 
2. 数据返回根据评分返回,如果评分过高的话,每次返回的ip都差不多,如果爬取速度过快怕被封ip.这个没测试,猜测.选取时,通过speed和score两个筛选数据的. 
3. 个别网站会被封.有几次xici代理直接封了ip可能跟那段时间重启程序有关. 
4. 自己有投机想法,直接在配置文件中配置目标网站.结果到后面目标网站把代理IP全封了.这个跟目标网站的反爬虫设置有关.为什么这么设置呢?因为项目返回的ip有时不能访问将爬取的网站.会出现失败.而scrapy自己又没有做太多处理,所以想提高代理Ip的有效性. 


  根据自己想法和实际情况,做了几点实现.主要为了保证代理ip的有效性. 

 1. 增加BloomFilter,作为抓取ip判重,减少判定使用资源.这里使用的是基于redis的版本.大材小用吧. [paramiao/pydrbloomfilter](https://github.com/paramiao/pydrbloomfilter)
 2. 使用redis作为数据存储和缓存. 
 3. 探测目标爬取网站时,增加cookie机制.目前主要有随机ua,代理IP,带cookie访问.cookie解析成字符串存放redis. 
 4. 通过Web方式公布api. http://0.0.0.0:1129/proxy/api/<num>  通过给定的num,返回num个代理ip.当前目前cookie只支持对一个目标站点,不支持爬取多个不同的目标网站.
 5. 代理通过轮询的方式给出. 
 6. 增加下限值判定.数据库中ip数目大于下限值时,不再启动程序获取ip. 
 7. 增加缓存,缓存一定数量的ip,每隔几分钟检验代理ip的有效性.

  TODO   
增加为爬取多个不同网址提供不同的代理池.原因是,碰到爬取多个不同网站代理ip不一定都能够生效.


## 安装
python 2.7版本
需要安装的软件:redis,lxml,gevent,redis-py,gevent,mmh3等.

### 安装redis
ubuntu系统可以直接运行:apt-get install redis-server

### 安装python扩展包
使用pip install命令安装redis lxml gevent mmh3等.

## 使用
配置:
这里说两点:
配置文件settings.py中
1.DEST_URL:目标网站,即将要爬取的网站.
2.TEST_URL:测试网站,为了web 缓存,取出一定数量的ip,每隔几分钟检验ip有效性,作为快速返回.

配置文件中的web cache:
是否启用缓存,先缓存一定数目的可用ip.检验速度较快.


启动
1.启动程序:python main.py
cmd.sh可以运行在ipproxy目录下运行的启停脚本,for linux
2.启动web接口:python web.py

