# -*- coding: utf-8 -*-

import logging
import logging.handlers
from random import Random

class IPProxyBase(object):
    def __init__(self,q):
        self.q = q
    def get_proxy():
        pass
    
MIN_NUM = 3000
#PROXY_RETRY_TIMES = 3
API_XICIDAILI_URL = "http://api.xicidaili.com/free2016.txt" # not use
#URL_LIST = ["XICIDAILI","KUAIDAILI","66IP","IP181",]
#URL_LIST = ["KUAIDAILI"]
URL_PATTERN = {
             "XICIDAILI": {
             "url":["http://www.xicidaili.com/nt/%d","http://www.xicidaili.com/nn/%d","http://www.xicidaili.com/wn/%d","http://www.xicidaili.com/wt/%d"],
             "ip":"//tr[@class='odd']/td[2]",
             "port":"//tr[@class='odd']/td[3]",
             "type":"//tr[@class='odd']/td[6]",
             "date":"//tr[@class='odd']/td[8]",
             "page_range":12
            },
            "KUAIDAILI":{
             "url":["http://www.kuaidaili.com/proxylist/%d","http://www.kuaidaili.com/free/inha/%d","http://www.kuaidaili.com/free/intr/%d","http://www.kuaidaili.com/free/outha/%d","http://www.kuaidaili.com/free/outtr/%d"],
             "ip":"//div[@id='freelist']/table/tbody/tr/td[1]",
             "port":"//div[@id='freelist']/table/tbody/tr/td[2]",
             "type":"//div[@id='freelist']/table/tbody/tr/td[4]",
             "page_range":12
            },
            "66IP":{
             "url":["http://www.66ip.cn/%d.html"],
             "ip":"//tbody/tr/td[1]",
             "port":"//tbody/tr/td[2]",
             "type":"//tbody/tr/td[3]",
             "page_range":12
            },
            "MIMIIP":{
             "url":["http://www.mimiip.com/","http://www.mimiip.com/gngao/%d","http://www.mimiip.com/gnpu/%d","http://www.mimiip.com/gntou/%d","http://www.mimiip.com/hw/%d"],
             "ip":"//tr/td[1]",
             "port":"//tr/td[2]",
             "type":"//tr/td[5]",
             "page_range":12
            },
            }   

PID = "PROXY_PID" # store process id for cmd.sh
TEST_URL = "https://www.baidu.com" #test url for web cache
#---rand str function-------------------------------
def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str
DEST_URL = [
    {
        "name":"douban",
        "url":"https://www.douban.com",
        "store_cookies": True,
        "use_default_cookies": True,
        "default_cookies":{"bid": random_str(11)},
        "num":50
    },
    {
        "name":"douban_api",
        "url":"https://api.douban.com/v2/movie/3237723",
        "store_cookies": True,
        "use_default_cookies": True,
        "default_cookies":{"bid":random_str(11)},
        "num":50
    },
]

#WHO = "http://www.xxorg.com/tools/checkproxy/"
WHO = {
        "xxorg":"http://www.xxorg.com/tools/checkproxy/",
        "3322":"http://members.3322.org/dyndns/getip"
      }
WHOAMI = "http://ip.42.pl/raw"
TEST_PROCESS_NUM = 3 # Test ip process number
STORE_COOKIE = False  # store cookie or not  for test url
USE_DEFAULT_COOKIE = False #request web with cookie or not for test url 
TYPES = ["http","https"]
SOCKET_TIMEOUT = 30  # used in TEST_URLS
QUEUE_TIMEOUT = 60  
REFRESH_WEB_SITE_TIMEER = 60*30 #
REFRESH_DB_TIMER = 60*60 #check ip in db
REFRESH_BF = 2 #time = REFRESH_BF *REFRESH_WEB_SITE_TIMEER
WORKER_NUM = 20

#---redis---------------------------------------
REDIS_SERVER = "127.0.0.1"
REDIS_PORT = 6379
DB_FOR_IP = 0
#---web cache----------------------------------
WEB_USE_REDIS_CACHE = True
#WEB_CACHE_IP_NUM = 60
WEB_CACHE_REFRESH = 60*3
#WEB_CACHE_REDIS = 2
REDIS_SET_CACHE = "web_cache_ip"
RETRY_TIMES = 1
#---redis for bloom filter----------------------
REDIS_CONNECTION = {
    'host': REDIS_SERVER,
    'port': REDIS_PORT,
    'db': 1,
    'bfkey': 'bf'}
#---default headers------------------------------
headers = {
         "Upgrade-Insecure-Requests" : "1",
         "Connection" : "keep-alive",
         "Cache-Control" : "max-age=0",
         "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
         "Accept-Encoding" : "gzip, deflate, sdch, br",
         
          }

#---user agent list---------------------------------
USER_AGENT_LIST = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",  
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",  
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",  
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",  
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",  
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",  
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",  
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",  
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",  
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",  
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",  
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24" ,
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
        "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
        "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
        "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
       ]

#---log --------------------------------------------------
log = logging.getLogger("proxy")
log.setLevel(logging.DEBUG)
fh = logging.handlers.TimedRotatingFileHandler("proxy.log", "D", 1, 10)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter("[%(asctime)s] [%(filename)24s] %(funcName)32s %(lineno)6s \
              %(levelname)6s - %(message)s", "%Y-%m-%d %H:%M:%S")
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)
log.addHandler(ch)
log.addHandler(fh)

# ip 测试  http://ip.filefab.com/index.php
#WHO = "http://www.xxorg.com/tools/checkproxy/"
#WHO = "http://members.3322.org/dyndns/getip"
# https://whoer.net/
#test local pc ip
#http://ip.42.pl/raw
#https://jsonip.com/
#http://httpbin.org/ip
#https://api.ipify.org/?format=json
#
