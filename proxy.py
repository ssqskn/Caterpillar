#coding:utf8
import re, time
import urllib2, requests
import multiprocessing

retry_times = 3
timeout_for_urlopen = 5
timeout_for_proxy_verify = 5

def urlopen(url):
    url_content = requests.get(url, timeout=timeout_for_urlopen).text
    print ">>Get content of ", url
    return url_content
    
def proxy_parser(raw_url_content):
    p = re.compile(r'\d+\.\d+\.\d+\.\d+:\d+')
    socket_info_list = p.findall(raw_url_content)
    return socket_info_list

def is_proxy_valid(proxy_addr):
    url_content = ""
    proxy_handler = urllib2.ProxyHandler({"http" : "http://%s:%s" 
                                          % (proxy_addr.split(":")[0], 
                                             proxy_addr.split(":")[1])})
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)
    
    for i in range(retry_times):
        try:
            url_content = urllib2.urlopen('http://www.qq.com', 
                                        timeout=timeout_for_proxy_verify).read()
            if len(url_content) > 0:
                print ">>Valid: Proxy of %s" % proxy_handler.proxies.values()[0]
                return (proxy_addr,True)
        except:
            continue
        
    print ">>Invalid: Proxy of %s" % proxy_handler.proxies.values()[0]
    return (proxy_addr,False)


class ProxySearcher():
    def __init__(self, is_get_url_by_crawler=False):
        self.dict = {}
        self.is_get_url_by_crawler = is_get_url_by_crawler
    
    def get_proxy_dict(self):
        return self.dict
            
    def search_proxy_list(self, urls=[]):
        if not self.is_get_url_by_crawler and len(urls) == 0:
            raise Exception, "Error: no urls provided."
        elif self.is_get_url_by_crawler:
            raise NotImplementedError
        
        ## get content of urls
        t0 = time.time()
        pool = multiprocessing.Pool(4)
        results = pool.map(urlopen, urls)
        pool.close()
        pool.join()
        print "Time spent for reading urls:", round((time.time()-t0),1),"secs"
        
        ## get proxy list
        t0 = time.time()
        pool = multiprocessing.Pool(30)
        proxy_results = pool.map(proxy_parser, results)
        pool.close()
        pool.join()
        
        ## verify proxy address
        for tmp in proxy_results:
            for proxy_addr in tmp:
                self.dict[proxy_addr] = {'status':'unverified', 'lastUsedTime':0}
        pool = multiprocessing.Pool(50)
        results = pool.map(is_proxy_valid, self.dict.keys())
        pool.close()
        pool.join()
        for res in results:
            if res[1]:
                self.dict[res[0]]['status'] = 'valid'
            else:
                self.dict[res[0]]['status'] = 'invalid'
         
        print "Time spent for parsing proxies:", round((time.time()-t0),1),"secs"
        print "Get %s proxies" % len(self.dict)
        
        with open("proxy/proxy" + str(long(time.time()/86400)) + ".txt",'w+') as f:
            for i in self.dict.iteritems():
                f.write(str(i) + "\n")
        
        
if __name__ == '__main__':
    proxy = ProxySearcher()
    
    urls = []
    for i in range(4200,4287):
        urls.append("http://www.youdaili.net/Daili/http/%s.html"%i)
    proxy.search_proxy_list(urls)
    