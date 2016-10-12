#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'Charles Chang'
import subprocess
import threading
import os
from  multiprocessing import Process,Pool

monitor_server="172.16.158.18"
conf_file="/tmp/conf/zabbix_sender_conf"
result_file="/tmp/result/monitor_data_"
server_list = ["mem_usage","cpu_percent","mem_percent","mem_limit"]

def sub_get_data(docker_name,server_name):
    get_cmd="/usr/local/zabbix/bin/zabbix_monitor_docker.py %s %s"%(docker_name,server_name)
    result=subprocess.Popen(get_cmd,stdout=subprocess.PIPE,shell=True)
    with open("%s%s"%(result_file,docker_name),'ab') as f:
        f.write('%s %s %s' %(docker_name,server_name,result.stdout.read()))

def get_data(docker_name):
    """获取数据，启动多线程获取多个监控项的数据"""
    with open("%s%s"%(conf_file,docker_name),'wb') as f:
        f.write("Hostname=%s\n"%docker_name)
    t_list = []
    for server_name in server_list:
        t = threading.Thread(target=sub_get_data,args=[docker_name,server_name,])
        t.start()
        t_list.append(t)
    for t in t_list:
        t.join()

def sender_data_single(docker_name):
    get_data(docker_name)
    send_cmd = """/usr/bin/zabbix_sender -c %s%s -z %s -i %s%s -r >/dev/null 2>&1""" %(conf_file,docker_name,
                                                                       monitor_server,result_file,docker_name)
    subprocess.call(send_cmd,shell=True)
    return docker_name

def remove_file(docker_name):
    """删除临时文件"""
    if os.path.isfile("%s%s"%(conf_file,docker_name)):
        os.remove("%s%s"%(conf_file,docker_name))
    if os.path.isfile("%s%s"%(result_file,docker_name)):
        os.remove("%s%s"%(result_file,docker_name))

def send_data():
    """调用多进程删除文件"""
    docker_cmd="""docker ps|awk 'NR>1{print $NF}'"""
    docker_namestr=subprocess.Popen(docker_cmd,stdout=subprocess.PIPE,shell=True)
    pool = Pool(5)
    for docker_name in docker_namestr.stdout.read().split('\n'):
        if docker_name:
            pool.apply_async(func=sender_data_single,args=(docker_name,),callback=remove_file)
    pool.close()
    pool.join()

if __name__ == "__main__":
    send_data()