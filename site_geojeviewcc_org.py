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
        self.get_html("https://www.geojeview.co.kr/Reservation/?date=%s" % yyyymmdd)
        #time.sleep(1)
        self.driver.implicitly_wait(5)
        login_uri = None
        id_xpath = '/html/body/div[3]/div/form/div/div[1]/dl[1]/dd/input'
        pw_xpath = '/html/body/div[3]/div/form/div/div[1]/dl[2]/dd/input'
        enter_xpath = '/html/body/div[3]/div/form/div/div[2]/input'
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
        reserv_key = 'https://www.geojeview.co.kr/Reservation/new/'
        form_uri="https://www.geojeview.co.kr/Reservation/?date=%s%s%s" % (yyyy,mm,dd,)
        self.get_html(form_uri)
        self.run_javascript("day_click('%s%s%s')" % (yyyy,mm,dd,))
        self.driver.implicitly_wait(10)
        ReserveSet = []

        timeout = 60
        waittime = 0.05
        max_idx = int(1.0 / waittime) * timeout

        #print("timeout: %dsec, waittime: %fsec, max_idx: %d" % (timeout, waittime, max_idx))

        for idx in range(max_idx):
            time.sleep(waittime)
            html = self.get_now_page()
            if reserv_key in html:
                print("find !!!")
                break
            elif '<tbody><tr><td colspan="6">예약 가능한 시간이 없습니다.</td>' in html:
                return False
            if idx > 5:
                print("yet : %d" % idx)

        if reserv_key not in html:
            return False

        lines = html.split("\n")
        
        history = []
        for line in lines:
            #if "예약하기" not in line:
            #    continue
            if reserv_key not in line:
                continue
            
            tok = line.split('"')
            for item in tok:
                if reserv_key not in item:
                    continue
                val = item.split(reserv_key)[1].split('"')[0]
                reservation_url = reserv_key + val
                if reservation_url in history:
                    continue

                history.append(reservation_url)

                result_dict = {
                        "time"      : val.split("/")[2],
                        "course"    : val.split("/")[1], # A=해돋이, B=해넘이
                        "yyyymmdd"  : val.split("/")[0],
                        "url"       : reservation_url,
                        }
                if result_dict["course"] == 'A':
                    result_dict["course"] = 0
                else:
                    result_dict["course"] = 1
                ReserveSet.append(result_dict)
        while True:
            if len(ReserveSet) == 0:
                return False
            bast_time = self.select_reservation_time(ReserveSet, hope_1st, hope_2nd, cource_index)
            #print("AAA : %s , %s %s  M<< %s" % (bast_time, hope_1st, hope_2nd, cource_index))
            ReserveSet.remove(bast_time)
            html = self.get_html(bast_time["url"])

            if '<input style="border: 0px;" type="submit" value="예약하기">' in html:
                self.click_buttion('//*[@id="ctl00_pnlMainCnt"]/div[4]/span[1]/input')
                #alart 예약완료 버튼 누르기
                try:
                    alert = self.driver.switch_to.alert
                    message = alert.text
                    self.log("message2: %s" % (message,))
                    alert.accept()
                    #alert.dismiss()
                except common.exceptions.NoAlertPresentException as e:
                    self.log("11112 : NO alarm %s " % e)
                    return False
                except common.exceptions.UnexpectedAlertPresentException as e:
                    self.log("UnexpectedAlertPresentException 2 %s " % e)
                print("예약완료 : %s" % (bast_time,))
                return True
            else:
                print("예약실패, 다른시간 재시도 : %s" % (bast_time,))
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


