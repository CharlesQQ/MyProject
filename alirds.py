#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import json
import time
import datetime
import os
import hashlib
import subprocess
from aliyunsdkcore import client
from aliyunsdkrds.request.v20140815 import  DescribeDBInstancesRequest
from aliyunsdkrds.request.v20140815 import DescribeRegionsRequest

class Check_Rds_Slow_Sql(object):
    def __init__(self,startTime):
        self.accesskey="LTAIAvWjED7tEhhb"
        self.accessSecret="UIkPkQRGvlsAiq5GGff9o5twqcvapx"
        self.startTime=startTime
    def get_DescribeRegions(self):
        region_request=DescribeRegionsRequest.DescribeRegionsRequest()
        region_request.set_accept_format('json')
        region_request.set_action_name('DescribeRegions')
        clt=client.AcsClient(self.accesskey,self.accessSecret,'cn-hangzhou')
        result=clt.do_action(region_request)
        data = json.loads(result)
        region_list = []
        for n in data['Regions']['RDSRegion']:
            region_list.append(n['RegionId'])
        region_list=list(set(region_list))
        return region_list

    def get_DBInstance(self):
        DBInstance_dic={}
        for regionId in self.get_DescribeRegions():
            clt=client.AcsClient(self.accesskey,self.accessSecret,regionId)
            request1=DescribeDBInstancesRequest.DescribeDBInstancesRequest()
            request1.set_action_name("DescribeDBInstances")
            request1.set_accept_format('json')
            try:
                result=clt.do_action(request1)
                data = json.loads(result)
                items=data['Items']['DBInstance']
                if items:
                    DBInstance_dic[regionId]=items[0]['DBInstanceId']
                else:
                    continue
            except Exception:
                pass
        return DBInstance_dic

    def slow_DBCheck(self):
        for region,instance in self.get_DBInstance().items():
            request=DescribeDBInstancesRequest.DescribeDBInstancesRequest()
            request.set_accept_format('json')
            request.set_action_name("DescribeSlowLogs")
            request.set_DBInstanceId(instance)
            request.add_query_param("StartTime",self.startTime)
            request.add_query_param("EndTime",time.strftime("%Y-%m-%dZ", time.gmtime()))
            clt=client.AcsClient(self.accesskey,self.accessSecret,region)
            try:
                result=clt.do_action(request)
                data=json.loads(result)["Items"]['SQLSlowLog']
                if data:
                    li = []
                    for i in range(len(data)):
                        MySQLTotalExecutionTimes=data[i]['MySQLTotalExecutionTimes']
                        MaxExecutionTime=data[i]['MaxExecutionTime']
                        SQLText=data[i]['SQLText']
                        DBName=data[i]['DBName']
                        CreateTime=data[i]['CreateTime']
                        li.append({'SQLText':SQLText,'DBName':DBName,'MySQLTotalExecutionTimes':MySQLTotalExecutionTimes,'MaxExecutionTime':MaxExecutionTime,'CreateTime':CreateTime})
                    return li
                else:
                    continue
            except Exception:
                pass

class Common_Method(object):
    def __init__(self):
        self.json_file='/tmp/Check_Rds_Slow_Sql.json'

    def getYesterday(self):
        today=datetime.date.today()
        oneday=datetime.timedelta(days=1)
        yesterday=str(today-oneday)+'Z'
        return yesterday

    def get_md5_value(self,str_value):
        myMd5 = hashlib.md5()
        myMd5.update(str_value)
        myMd5_Digest = myMd5.hexdigest()
        return myMd5_Digest

    def Alert_Date(self):
        Alert_Item=Check_Rds_Slow_Sql(self.getYesterday())
        try:
            if os.path.isfile(self.json_file):
                with open(self.json_file,'rb') as f:
                    data = json.load(f)
                    if data:
                        real_data= Alert_Item.slow_DBCheck()
                        for item in real_data:
                            li = []
                            if item not in data:
                                li.append(item['DBName'])
                                li.append(self.get_md5_value(item['SQLText']))
                                li.append("%s"%json.dumps(item))
                                li.insert(0,"python")
                                li.insert(1,"monitor.py")
                                subprocess.call(li, shell=False)
                            else:
                                continue
            else:
                with open(self.json_file,'wb') as f:
                    pass
        except Exception:
            pass
        finally:
            os.remove(self.json_file)

        with open(self.json_file,'ab') as f:
            json.dump(Alert_Item.slow_DBCheck(),f)

if __name__ == '__main__':
    My_Item=Common_Method()
    My_Item.Alert_Date()