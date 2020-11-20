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
from selenium import common


class robotTest(robotBase):
    def __init__(self, webdriver_path, domain, visible=True, proxy_ipaddr=None, proxy_port=None):
        robotBase.__init__(self, webdriver_path, domain, visible, proxy_ipaddr, proxy_port)
        pass

def main():
    bot = robotTest("./chromedriver", "www.seleniumeasy.com")
    html = bot.get_html("test/javascript-alert-box-demo.html")


    #bot.run_javascript("myConfirmFunction()")
    try:
        alert = bot.driver.switch_to.alert
        message = alert.text
        alert.accept()
    except common.exceptions.NoAlertPresentException as e:
        print("11111 : NO alarm %s " % e)
    except common.exceptions.UnexpectedAlertPresentException as e:
        print("111111 %s " % e)
    html = bot.get_now_page()

    bot.run_javascript("myAlertFunction()")
    sleep(2)
    try: 
        html = bot.get_now_page()
    except common.exceptions.UnexpectedAlertPresentException as e:
        pass
        #alert = bot.driver.switch_to.alert
        #message = alert.text
        #alert.accept()
    html = bot.get_now_page()
    time.sleep(200)
    return

if __name__ == "__main__":
    main()

