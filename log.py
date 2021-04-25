#-*-coding:utf-8-*-
import os
import sys
import time
from time import sleep
import requests
import threading
from common import *
from dialog import *
import platform

sys.path.append("paramiko")
import base64
import paramiko
import getpass

def main():
    #cli = paramiko.SSHClient()
    #cli.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    log_pwd = base64.b64decode(b'c3lzdGVtX0FBQQ==')[0:-4].decode('utf-8')
    log_id =  base64.b64decode(b'ZWx1b25fQkJC')[0:-4].decode('utf-8')
    log_port =  base64.b64decode(b'NDIwMDBfQ0ND')[0:-4].decode('utf-8')
    log_ip =  base64.b64decode(b'MjIyLjk5LjE3OC45X0RERA==')[0:-4].decode('utf-8')
    print(log_pwd)
    
    #cli.connect(server, port=22, username=user, password=pwd)
    #stdin, stdout, stderr = cli.exec_command("ls -la")
    #lines = stdout.readlines()
    #print(''.join(lines))
     
    #cli.close()

def mk_b64():
    ddd=base64.b64encode(b"_DDD")
    ccc=base64.b64encode(b"_CCC")
    bbb=base64.b64encode(b"_BBB")
    aaa=base64.b64encode(b"_AAA")
    print("%s" % (aaa,))
    print("%s" % (bbb,))
    print("%s" % (ccc,))
    print("%s" % (ddd,))


if __name__ == "__main__":
    main()
    #main()
