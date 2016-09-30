#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'Charles Chang'
import json
import urllib2
import collections

class CreateScreen(object):

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
        url = "http://zabbix.i.beebank.com/api_jsonrpc.php"
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

    def __gethostIDs(self):
        data = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": "extend",
            },
            "auth": self.login(),
            "id": 1
        }
        hostids=[]
        hostname =[]
        for item in self.request(data)['result']:
            hostids.append(item['hostid'])
            hostname.append(item['name'])
        return hostids


    def getgrapsID(self):
        data = {
        "jsonrpc": "2.0",
        "method": "graph.get",
        "params": {
            "output": "extend",
            "hostids": self.__gethostIDs(),
            "sortfield": "name"
        },
        "auth": self.login(),
        "id": 1
        }
        grapid_dic = {}
        for grapitem in self.request(data)['result']:
            grapid_dic[grapitem['name']]=grapitem['graphid']
        screenitems = collections.defaultdict(list)
        for k,v in grapid_dic.items():
            if k.startswith(u'容器'):
                screenitems[k.split()[0]].append(v)
        return screenitems    #返回group名称列表和数量

    def create(self,username):        #根据graphid号创建screen
        a,b = divmod(len(self.getgrapsID()[username]),2)
        hsize = a if b==0 else a+1
        screenitems_li=[]
        for item in self.getgrapsID()[username]:
            screenitems_li.append({
            "resourcetype": 0,
            "resourceid": item,
            "rowspan": 1,
            "colspan": 1,
            "x": len(screenitems_li) %2,
            "y": len(screenitems_li)/2,
            "width": 500,
            "height": 100
            })
        data ={
            "jsonrpc": "2.0",
            "method": "screen.create",
            "params": {
                "name": "%s_screen" %username,
                "hsize":hsize,
                "vsize": 2,
                "screenitems":screenitems_li,
            },
            "auth": self.login(),
            "id": 1
        }
        response=self.request(data)
        print response
        return response

    def screenget(self):
        data = {
        "jsonrpc": "2.0",
        "method": "screen.get",
        "params": {
            "output": "extend",
        },
        "auth": self.login(),
        "id": 1
    }
        response = self.request(data)['result']
        screenid_li = []
        for item in response:
            screenid_li.append(item['screenid'])
            #screenid
        return screenid_li

    def screenitemget(self):
        data = {
            "jsonrpc": "2.0",
            "method": "screenitem.get",
            "params": {
                "output": "extend",
                "screenids": self.screenget()
            },
            "auth": self.login(),
            "id": 1
        }
        screenitem_dic =collections.defaultdict(list)
        response = self.request(data)['result']
        for screen in response:
            screenitem_dic[screen['screenid']].append(screen['screenitemid'])
        return screenitem_dic    #返回screen信息字典，key为screen的id，value为screenitem的ID

    def screenitemupdate(self,screenid,screenitemid):
        print screenitemid
        data={
            "jsonrpc": "2.0",
            "method": "screenitem.update",
            "params": {
                'screenid':screenid,
                "screenitemid": screenitemid,
                "width": 500,
                "height": 100
            },
            "auth": self.login(),
            "id": 1
        }
        response =self.request(data)
        print response
        return response

    def screendelete(self):
        data ={
            "jsonrpc": "2.0",
            "method": "screen.delete",
            "params": self.screenget(),
            "auth": self.login(),
            "id": 1
        }
        response = self.request(data)
        print response
        return response
if __name__ == '__main__':
    instance=CreateScreen()
    #instance.screendelete()
    print "Begin to create screen"
    for username in instance.getgrapsID().keys():
        instance.create(username)