#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'Charles Chang'
import json
import urllib2

class CreateScreen(object):
    def __init__(self,username):
        self.username=username

    def login(self):
        data = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": "Admin",
                "password": "zabbix"
            },
            "id": 1
            }
        response= self.request(data)
        return response['result']

    def request(self,data):
        url = "http://zabbix.i.bbtfax.com/api_jsonrpc.php"
        header = {"Content-Type": "application/json"}
        data = json.dumps(data)
        request = urllib2.Request(url,data)
        for key in header:
            request.add_header(key,header[key])
        try:
            result=urllib2.urlopen(request)
        except Exception as e:
            print e
        else:
            response = json.loads(result.read())
            result.close()
            return response

    def __gethostIDs(self,hostname):
        data = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": "extend",
                "filter": {
                    "host": [
                        hostname,
                    ]
                }
            },
            "auth": self.login(),
            "id": 1
        }
        hostids = self.request(data)['result'][0]['hostid']
        return hostids


    def __getgrapsID(self):
        data = {
        "jsonrpc": "2.0",
        "method": "graph.get",
        "params": {
            "output": "extend",
            "hostids": self.__gethostIDs(self.username),
            "sortfield": "name"
        },
        "auth": self.login(),
        "id": 1
        }
        grapid_list = []
        for grapitem in self.request(data):
            grapid_list.append(grapitem['graphid'])
        return grapid_list,len(grapid_list)     #返回group名称列表和数量

    def create(self):
        a,b = divmod(self.__getgrapsID()[1],2)
        hsize = a if b==0 else a+1
        screenitems = []
        for item in self.__getgrapsID()[0]:
            screenitems.append({
            "resourcetype": 0,
            "resourceid": item,
            "rowspan": 0,
            "colspan": 0,
            "x": 0,
            "y": 0}
            )
        data ={
            "jsonrpc": "2.0",
            "method": "screen.create",
            "params": {
                "name": "%s_screen" %self.username,
                "hsize":hsize,
                "vsize": 2,
                "screenitems":screenitems,
            },
            "auth": self.login(),
            "id": 1
        }
        response=self.request(data)
        return response

if __name__ == '__main__':
    instance=CreateScreen("ZhuBang Docker_158.5")
    instance.create()