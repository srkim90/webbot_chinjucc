#-*-coding:utf-8-*-
import os
import re
import sys
import time
import datetime
import requests
import threading
from common import *
from dialog import *
from datetime import timedelta
import platform
import hashlib
import copy

class robotGeojeViewcc(robotBase):
    def __init__(self, webdriver_path, domain, visible=True, proxy_ipaddr=None, proxy_port=None):
        robotBase.__init__(self, webdriver_path, domain, visible, proxy_ipaddr, proxy_port)
        self.log_handeler = g_log_fn
        self.exit_check_fn = g_exit_check_fn
        self.n_tabs = 1

    def do_login(self, uid, passwd, yyyymmdd):
        self.get_html("https://www.geojeview.co.kr/auth/login")
        #time.sleep(1)
        self.driver.implicitly_wait(5)
        login_uri = None
        id_xpath = '/html/body/div[3]/div/form/div/div[1]/div[3]/div[1]/ul/li[1]/div/input'
        pw_xpath = '/html/body/div[3]/div/form/div/div[1]/div[3]/div[1]/ul/li[2]/div/input'
        enter_xpath = '/html/body/div[3]/div/form/div/div[1]/div[3]/div[2]/div/button'
        nErr =  super().do_login(uid, passwd, login_uri, id_xpath, pw_xpath, enter_xpath)

        window_handles = self.driver.window_handles
        for idx, item in enumerate(window_handles[1:]):
            self.driver.switch_to.window(item)
            self.driver.close()
        self.driver.switch_to.window(window_handles[0])

        return nErr

    #except_list = [("10:05", 1),  ("10.55", 1), ..  ]
    def select_reservation_time(self, ReserveSet, hope_time, hope_time2, course, except_list=None):
        if hope_time2 == None:
            hope_time2 = hope_time
        hh = hope_time.split(":")[0]
        mm = hope_time.split(":")[1]
        _hope_time = (int(hh)*60) + int(mm)
        hh = hope_time2.split(":")[0]
        mm = hope_time2.split(":")[1]
        _hope_time2 = (int(hh)*60) + int(mm)
        last_dalta = 999999
        bast_item  = None
        last_dalta2 = 999999
        bast_item2  = None
        for idx in range(2):
            for item in ReserveSet:
                if course != item["course"] and idx == 0:
                    continue
                _hhmm = item["time"]
                if except_list != None:
                    for except_item in except_list:
                        except_time = except_item[0]
                        except_cource = except_item[1]
                    if except_time == _hhmm and idx == except_cource:
                        continue
                _hh   = _hhmm[0:2]
                _mm   = _hhmm[2:4]
                available_time = (int(_hh)*60) + int(_mm)
                time_delta  = abs(_hope_time  - available_time)
                time_delta2 = abs(_hope_time2 - available_time)
                if last_dalta > time_delta:
                    bast_item = item
                    #print("%s %s %s : %s :%s" % (item, time_delta, last_dalta, _hhmm, available_time))
                    last_dalta = time_delta
                if last_dalta2 > time_delta2:
                    bast_item2 = item
                    last_dalta2 = time_delta2

            if bast_item != None:
                break
        if last_dalta > last_dalta2 + 60:
            return bast_item2
        return bast_item


    def parser_reservation_time(self, html):
        if type(html) == 'bytes':
            html = html.decode('utf-8')
        htmls = html.split("\n")
        f_start = False
        f_tr = False
        in_tr = 0
        ReserveSet = []
        for line in htmls:
            if 'table' in line:
                f_start = True
                continue
            elif '</table>' in line:
                f_start = False
                continue
            if '<tr>' in line:
                f_tr = True
                in_tr = 0
                continue
            elif '</tr>' in line:
                f_tr = False
                continue
        
            if f_start == False or f_tr == False:
                continue

            if "ReserveCheck" not in line and '<td></td><td></td><td></td>' not in line:
                continue
            in_tr += 1
            #line = line.decode('utf-8')

            line = line.split("<td>")
            _time = line[1].split('<')[0]
            _hole = line[2].split('<')[0]

            if _time == "":
                continue
            _javascript = line[3].split('"')[1]

            item = {
                    "course"        : in_tr,
                    "time"          : _time,
                    "hole"          : _hole,
                    "javascript"    : _javascript,
            }
            ReserveSet.append(item)
        return ReserveSet


    def do_reservation(self, yyyymmdd, hope_1st, hope_2nd, cource_index): #6,7,8,11,12,13,14

        yyyy = yyyymmdd[0:4]
        mm   = yyyymmdd[5:7]
        dd   = yyyymmdd[8:10]
        form_uri="https://www.geojeview.co.kr/booking"
        html = self.get_html(form_uri)

        lines = html.split("\n")
        ln_table = 0
        ln_tr = 0
        ln_td = 0
        xpath = None
        yyyymmdd2 = yyyymmdd.replace("-", "")
        for line in lines:
            if '<table class="booking-calendar table table-bordered date-info">' in line:
                ln_table += 1
                ln_tr = -1
                ln_td = 0
            if '<tr>' in line: 
                ln_tr += 1
                ln_td = 0
            if '<td class="' in line: 
                ln_td += 1

            if yyyymmdd2 in line:
                if 'completed' in line:
                    return "[%s] 해당일자 예약 완료되었습니다." % yyyymmdd
                xpath='//*[@id="booking-index"]/div[1]/table[%d]/tbody/tr[%d]/td[%d]/a' % (ln_table, ln_tr, ln_td)
                break
        
        if xpath == None:
            return False
        print("selected : yyyymmdd=%s, xpath=%s" % (yyyymmdd, xpath))
        self.click_buttion(xpath)

        self.driver.implicitly_wait(60)
        time.sleep(1.25)
        ReserveSet = []

        html = self.get_now_page()
        lines = html.split("\n")

        ln_tr = 0
        for line in lines:
            #<button type="button" class="btn btn-sm btn-primary btn-booking" data-date="20210426" data-cours="B" data-time="0644" data-hole="18">예약
            if "btn btn-sm btn-primary btn-booking" in line:
                ln_tr += 1
                xpath = '//*[@id="booking-index"]/div[2]/div/div/table/tbody/tr[%d]/td[5]/button' % (ln_tr,)
                time_hhmm = line.split('data-time="')[-1].split('"')[0]
                time_yyyymmdd = line.split('data-date="')[-1].split('"')[0]
                cours = line.split('data-cours="')[-1].split('"')[0]
                result_dict = {
                        "time"      :time_hhmm,
                        "course"    :cours, # A=해돋이, B=해넘이
                        "yyyymmdd"  :time_yyyymmdd,
                        "url"       : xpath,
                        }
                ReserveSet.append(result_dict)

        while True:
            if len(ReserveSet) == 0:
                return False
            bast_time = self.select_reservation_time(ReserveSet, hope_1st, hope_2nd, cource_index)
            #print("AAA : %s , %s %s  M<< %s" % (bast_time, hope_1st, hope_2nd, cource_index))
            ReserveSet.remove(bast_time)

            xpath = bast_time["url"]
            self.click_buttion(xpath) # 예약 버튼
            self.driver.implicitly_wait(60)
            #html = self.get_now_page()
            #if "약관 동의 및 예약 완료" not in html:
            #    print('not exist : 약관 동의 및 예약 완료 %s' % bast_time)
            #    continue
            summit_xpath = '//*[@id="form-create"]/div[8]/button[1]' # 약관 동의 및 예약 완료 팝업 누르기

            try:
                self.click_buttion(summit_xpath)
                self.driver.implicitly_wait(60)
                time.sleep(1.25)

                alert = self.driver.switch_to.alert
                message = alert.text
                self.log("message2: %s" % (message,))
                alert.accept()
            except Exception as e:
                err_str = "예약실패, 다른시간 재시도 : %s, Error str = %s" % (bast_time, e)
                print(err_str)
                continue

        return False



def GeojeViewccMain(input_param, log_fn, exit_check_fn):
    global g_log_fn
    global g_exit_check_fn
    g_log_fn = None
    g_exit_check_fn = None#exit_check_fn

    if platform.system() != "Windows":
        chromedriver = "./chromedriver"
    else:
        chromedriver = "chromedriver_86.0.4240.22.exe"
    
    try:
        bot = robotGeojeViewcc(chromedriver, "geojeview.co.kr")
    except Exception as e:
        errstring = "웹크롤러 로딩 실패\n%s" (e,)
        del bot
        return errstring

    #{'QTextEdit': {'아이디': '', '비밀번호': ''}}
    try:
        uid = input_param["QTextEdit"]["아이디"]
        pwd = input_param["QTextEdit"]["비밀번호"]
        day = input_param["QTextEdit"]["날짜"]
        hope_1st = check_time_validation(input_param["QTextEdit"]["희망시간1"])
        hope_2nd = check_time_validation(input_param["QTextEdit"]["희망시간2"])
        cource_index = input_param["QComboBox"]["코스선택"] + 1
        run_mode = input_param["QComboBox"]["모드선택"] + 1
        if hope_2nd == None:
            hope_2nd = hope_1st
        else:
            hope_2nd = hope_2nd.replace(" ", "")
            if len(hope_2nd) == 0:
                hope_2nd = hope_1st

    except KeyError as e:
        bot.log("Error. 파라미터 산출 실패 (%s), json:%s" % (e, input_param))   
        del bot
        return "Error. 파라미터 산출 실패 (%s), json:%s" % (e, input_param)
 
    uid_whitelist = ["c93d5717ef8620854765eb79c144f80e", 
                     "06a4d20f05d65e93687f830f84818895",
                     "1ef1cbb6f81fd5ab92745ac379e78fda",
                     "5f45958e26581994817ede7551ed4cfa",
                     "55b05110605658e51b66eafff7d28ce9",
                     "b21a2045433543ae98d82a71006acd59",
                     "6e5a84e470f9c959b653cdf584f4c6b0",
                     "232d6b607ae0c4cac7ce9aa3b56386c4", 
                     ]
       


    uid_md5 = hashlib.md5()
    uid_binary = "%s\n" % (uid,)
    uid_md5.update(uid_binary.encode("utf-8"))
    uid_md5 = uid_md5.hexdigest()
    print("uid_md5 : %s" % uid_md5)
    if uid_md5 not in uid_whitelist:
        return "[Error] 미등록 ID 입니다. 관리자에게 등록 요청을 하셔야 이용 가능 합니다"

    if len(uid) <= 0 or len(pwd) <= 0:
        bot.log("ID/PW 미입력")   
        del bot
        return "ID/PW 미입력"

    if bot.do_login(uid, pwd, day) == False:
        bot.log("Login fail!!")
        del bot
        return "로그인에 실패 하였습니다"
    bot.log("Login success!!")

    #print("OK  !!!")
    #return "END"

    time.sleep(1)
    while True:
        try:
            nErr = bot.do_reservation(day, hope_1st, hope_2nd, cource_index)
            if nErr == True:
                break
            elif nErr == False:
                pass
            else:
                del bot
                return nErr
            now = datetime.now()
            now_hhmm = now.hour * 100 + now.minute
            if now_hhmm < 950 or now_hhmm > 1010:
                time.sleep(3.5)
            else:
                time.sleep(0.25)
        except common.exceptions.NoSuchWindowException as e:
            break
    while True:
        try:
            aaaa = bot.driver.page_source
        except Exception as e:
            print("e : %s" % e)
            break
        time.sleep(2)
    return True


