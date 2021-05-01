#-*-coding:utf-8-*-

import os
import sys
import time
import gzip
import datetime
import requests
import threading
import zipfile
import shutil
import platform
import urllib.request
import subprocess
from datetime import timedelta
from selenium import webdriver
from selenium import common
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# pip install selenium 
# sudo yum install ImageMagick
# ps -ef | grep chrome | grep google  | awk '{print $2}' | xargs kill -9

class robotBase():
    def __init__(self, webdriver_path, domain, visible=True, proxy_ipaddr=None, proxy_port=None):
        self.log_path = "logs"
        self.log_handeler = None
        self.exit_check_fn = None
        self.driver  = self.__get_driver(webdriver_path, visible, proxy_ipaddr, proxy_port)
        self.domain  = domain
        self.now_url = None
        self.schim = "https://"
        return

    def __del__(self):
        if self.driver != None:
            try:
                self.driver.close()
            except:
                pass
        return

    def log(self, logstring, lv=0, e=None):
        log_all = "%s" % logstring
        if e != None:
            log_all += "\n   --> %s" % e
        if self.log_handeler == None:
            print(log_all)
        else:
            print(log_all)
            self.log_handeler(log_all, lv)
        if self.log_path != None:
            #now = datetime.datetime.now()
            now = time.localtime()
            yymmdd = "%s%02d%02d.log" % (now.tm_year, now.tm_mon, now.tm_mday)
            if os.path.exists(self.log_path,) == False:
                os.makedirs(self.log_path)
            logfile = os.path.join(self.log_path, yymmdd)
            with open(logfile, "a") as fd:
                timestemp = time.strftime('%H:%M:%S', time.localtime(time.time()))
                log_all = "[%s] %s" % (timestemp, log_all)
                fd.write("%s\n" % log_all)
        return

    def __get_driver(self, webdriver_path, visible, proxy_ipaddr, proxy_port):
        chrome_options = webdriver.ChromeOptions()
        if proxy_ipaddr != None and proxy_port != None:
            PROXY = "%s:%d" % (proxy_ipaddr, proxy_port)
            proxyDict = { 
                    "http"  : PROXY,
                    "https" : PROXY,
                    }

            #chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument('--proxy-server=%s' % PROXY)
        if visible != True:
            chrome_options.add_argument('--headless')
        driver = None
        for n_retry in range(2):
            try:
                driver = webdriver.Chrome(webdriver_path, chrome_options=chrome_options)
                break
            except Exception as e:
                self.log("[Error] Fail to load chromdriver : SessionNotCreatedException", e = e)
                webdriver_path = self.__get_chromdriver(e)
        if driver == None:
            return None
        driver.implicitly_wait(1)
        return driver

    def __get_chromdriver(self, error):
        if platform.system() != "Windows":
            return None
        strexception = "%s" % error
        try:
            #cmd=['wmic', 'datafile', 'where', 'name=C:\\Program\ Files\ (x86)\\Google\\Chrome\\Application\\chrome.exe', 'get', 'Version', '/value']
            cmd=['reg', 'query', 'HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon', '/v', 'version']
            #cmd=['wmic', 'datafile where name="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" get Version /value']
            #current_browser_ver = int(strexception.split("Current browser version is")[1].split(".")[0].replace(" ", ""))
            #wmic datafile where name="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" get Version /value
            out = subprocess.check_output(cmd).decode("utf-8")
            current_browser_ver = out.split("REG_SZ")[-1].split(" ")[-1]
            current_browser_ver = current_browser_ver.replace("\r", "")
            current_browser_ver = current_browser_ver.replace("\n", "")
            current_browser_ver = int(current_browser_ver.split(".")[0])
        except Exception as e:
            self.log("[Error] Fail to get current browser version : %s" % (strexception,)) # session not created: This version of ChromeDriver only supports Chrome version 80
            return None
        url = "https://chromedriver.chromium.org/downloads"
        response = requests.get(url)
        response = response.text.split("index.html?path=")[1:]
        self.log("response size : %s" % len(response))
        for line in response:
            full_version = line.split("/")[0]
            maj_version = int(full_version.split(".")[0])
            if maj_version != current_browser_ver:
                self.log("maj_version=%s, current_browser_ver=%s" % (maj_version, current_browser_ver))
                continue

            new_name = "chromedriver_%s.exe" % full_version
            if os.path.exists(new_name) == True:
                self.log("exist now version : %s return it.." % new_name)
                return new_name

            url = "https://chromedriver.storage.googleapis.com/%s/chromedriver_win32.zip" % (full_version,)
            file_name = "chromedriver_win32_%s.zip" % full_version
            urllib.request.urlretrieve(url, file_name)
            if os.path.exists(file_name) == False:
                self.log("download chrome driver fail." % url)
                return None
            with zipfile.ZipFile(file_name) as zf:
                zf.extractall()
            os.remove(file_name)
            file_name = "chromedriver.exe"
            shutil.copy(file_name, new_name)
            self.log("download chrome driver OK (%s)" % new_name)
            return new_name
        self.log("No download data")
        return None

    def get_myip(self):
        self.driver.get("https://www.infobyip.com")
        source = self.driver.page_source
        ipaddr = source.split("<a href=\"/traceroute-")[1].split(".html")[0]
        self.log("myipaddr: %s" % ipaddr)
        return ipaddr

    def get_html(self, resource_uri, waitclass=None):
        if self.driver == None:
            return None
        if "https://" in resource_uri or "http://" in resource_uri:
            url = resource_uri
        else:
            url = "%s%s/%s" % (self.schim, self.domain, resource_uri)
        #self.log("get_html : url=%s" % url)
        try:
            self.driver.implicitly_wait(10)
            self.driver.get(url)
            self.driver.implicitly_wait(60)
            #if waitclass != None:
            #    wait = WebDriverWait(self.driver, 3)
            #    try:
            #        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, waitclass)))
            #    except:
            #        pass
        except Exception as e:
            self.log("[Error] Fail to get html : URL=%s" % (url,), e=e)
            return None
        source = self.driver.page_source
        self.now_url = url
        return source

    def selectDropbox(self, element_id, target_name):
        dropbox = self.driver.find_element_by_id(element_id)
        sel_dropbox = Select(dropbox)
        sel_dropbox.select_by_visible_text(target_name)
        return

    def run_javascript(self, script):
        self.driver.execute_script(script)
        self.driver.implicitly_wait(3)

    def get_now_page(self):
        html = self.driver.page_source
        nowtime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.%f')
        if platform.system() == "Windows":
            return html
        file_name = "./html/%s.html.gz" % (nowtime,)
        with gzip.open(file_name, "wb") as fd:
            b_html = html.encode("utf-8")
            fd.write(b_html)
        return html

    def __input_form(self, element_xpath, input_text):
        #self.log("input form : %s" % input_text)
        if self.driver == None:
            return False
        try:
            elem_login = self.driver.find_element_by_xpath(element_xpath)
        except Exception as e:
            self.log("[Error] Fail to input text to form : element_xpath=%s, URL=%s" % (element_xpath, self.now_url,), e=e)
            return False
        elem_login.send_keys(input_text)
        return True

    def click_buttion(self, xpath):
        self.log("click buttion : xpath=%s" % xpath)
        if self.driver == None:
            return False
        try:
            #elem_login = self.driver.find_element_by_xpath(xpath).send_keys(Keys.RETURN)
            elem_login = self.driver.find_element_by_xpath(xpath).click()
        except Exception as e:
            self.log("[Error] Fail to click buttion : xpath=%s, URL=%s" % (xpath, self.now_url,), e=e)
            return False
        return True

    def do_login(self, uid, passwd, login_uri, id_xpath, pw_xpath, enter_xpath):
        if login_uri != None:
            if self.get_html(login_uri) == None:
                self.log("[Error] Fail to get login page")
                return False

        if self.__input_form(id_xpath, uid) == False:
            self.log("[Error] Fail to found id form")
            return False

        if self.__input_form(pw_xpath, passwd) == False:
            self.log("[Error] Fail to found password form")
            return False

        if self.click_buttion(enter_xpath) == False:
            self.log("[Error] Fail to found submit buttion")
            return False

        try:
            time.sleep(1.5)
            test_url = "%s%s" % (self.schim, self.domain, )
            if self.get_html(test_url) == None:
                return False
        except Exception as e:
            return False

        return True

    def write_comment(self, input_text, form_uri, form_xpath, enter_xpath):
        source = self.get_html(form_uri)
        if source == None:
            self.log("[Error] Fail to get form page")
            return False

        time.sleep(1)

        if self.__input_form(form_xpath, input_text) == False:
            self.log("[Error] Fail to found input form")
            return False

        time.sleep(1)

        if self.click_buttion(enter_xpath) == False:
            self.log("[Error] Fail to found submit buttion")
            return False
        return source

