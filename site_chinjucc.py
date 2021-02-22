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

class robotChinjucc(robotBase):
    def __init__(self, webdriver_path, domain, visible=True, proxy_ipaddr=None, proxy_port=None):
        robotBase.__init__(self, webdriver_path, domain, visible, proxy_ipaddr, proxy_port)
        self.log_handeler = g_log_fn
        self.exit_check_fn = g_exit_check_fn
        self.n_tabs = 1

    def do_login(self, uid, passwd):
        self.get_html("https://chinjucc.co.kr/main")

        window_handles = self.driver.window_handles
        for idx, item in enumerate(window_handles[1:]):
            self.driver.switch_to.window(item)
            self.driver.close()
        self.driver.switch_to.window(window_handles[0])

        if self.click_buttion('//*[@id="header"]/div/div[2]/div[2]/a') == False:
            self.log("[Error] Fail to found submit buttion")
            return False
        self.get_html("https://www.chinjucc.co.kr/Join/Login.aspx")
        time.sleep(1)
        self.driver.implicitly_wait(5)
        login_uri = None
        id_xpath = '//*[@id="ctl00_ContentPlaceHolder1_txtUserID"]'
        pw_xpath = '//*[@id="ctl00_ContentPlaceHolder1_txtPassword"]'
        enter_xpath = '//*[@id="ctl00_ContentPlaceHolder1_lbtLogin"]'
        nErr =  super().do_login(uid, passwd, login_uri, id_xpath, pw_xpath, enter_xpath)
        return nErr

    def init_working_tab(self, yyyymmdd, n_tabs=16):
        yyyy = yyyymmdd[0:4]
        mm   = yyyymmdd[5:7]
        dd   = yyyymmdd[8:10]
        self.n_tabs = n_tabs
        tabs = self.driver.window_handles
        for idx in range(n_tabs):
            body = self.driver.find_element_by_tag_name("body")
            body.send_keys(Keys.CONTROL + 't')
            self.driver.execute_script('window.open("about:blank", "_blank");')
            self.log("open tab : idx=%d" % (idx, ))
            self.driver.switch_to_window(self.driver.window_handles[idx+1])
            self.driver.get('https://www.chinjucc.co.kr/Reservation/Reservation.aspx')

        while True:
            for idx in range(n_tabs):
                print("switch-tab : %s" % idx + 1)
                self.driver.get('https://www.chinjucc.co.kr/Reservation/Reservation.aspx')
                self.driver.switch_to_window(self.driver.window_handles[idx+1])
                next_javascript="javascript:moveCalendar(1);"
                while True:
                    html = self.get_now_page()
                    html_yyyy = html.split("년")[0].split(">")[-1]
                    #html_mm   = html.split("월")[0].split(">")[-1]
                    html_mm   = "%02d" % int(html.split("월")[0].split(">")[-1])
                    #print("%s %s %s html:%s %s" % (yyyy, mm, dd, html_yyyy, html_mm))
                    if html_yyyy == yyyy and html_mm == mm:
                        break
                    try:
                        self.run_javascript(next_javascript)
                        self.driver.implicitly_wait(10)
                    except:
                        self.log("Error in switch tab, idx=%d" % idx)
                        return False
                    time.sleep(0.1)
           
        self.driver.switch_to_window(tabs[0])
        return

    def do_reservation_test(self, yyyymmdd, hope_1st, hope_2nd): #6,7,8,11,12,13,14
        form_uri="https://www.chinjucc.co.kr/Reservation/ReservationWait.aspx"
        next_javascript="javascript:moveCalendar(1);"
        dropbox1_id="ctl00_ContentPlaceHolder1_ddlHopeTime1"
        dropbox2_id="ctl00_ContentPlaceHolder1_ddlHopeTime2"
        yyyy = yyyymmdd[0:4]
        mm   = yyyymmdd[5:7]
        dd   = yyyymmdd[8:10]
        html = self.get_html(form_uri)
        while True:
            html = self.get_now_page()
            html_yyyy = html.split("년")[0].split(">")[-1]
            #html_mm   = html.split("월")[0].split(">")[-1]
            html_mm   = "%02d" % int(html.split("월")[0].split(">")[-1])
            #print("%s %s %s %s %s" % (yyyy, mm, dd, html_yyyy, html_mm))
            if html_yyyy == yyyy and html_mm == mm:
                break
            try:
                self.run_javascript(next_javascript)
                self.driver.implicitly_wait(10)
            except:
                return False
            time.sleep(1)
        time.sleep(0.5)
        MAX_RETRY=10
        for idx in range(MAX_RETRY):
            try:
                html = self.get_now_page()
                break
            except:
                time.sleep(0.25)
                if idx == MAX_RETRY - 1:
                    self.log("[Error] !! max retry : 10")
                    return False
                continue
        js_key = "javascript:GetTimeList('%s'" % yyyymmdd
        if js_key not in html:
            return False
        reservation = html.split(js_key)[1].split(";")[0]
        reservation = "%s%s;" % (js_key, reservation)
        try:
            self.run_javascript(reservation)
        except:
            return False
        time.sleep(0.5)

        hope_1st = hope_1st.split(":")[0]
        hope_2nd = hope_2nd.split(":")[0]

        self.selectDropbox(dropbox1_id, "%02d시대" % int(hope_1st))
        self.selectDropbox(dropbox2_id, "%02d시대" % int(hope_2nd))
        self.driver.implicitly_wait(10)
        time.sleep(0.5)

        try:
            buttion_id = "ctl00_ContentPlaceHolder1_lbtOK"
            elem_login = self.driver.find_element_by_id(buttion_id).click()
        except Exception as e:
            self.log("[Error] Fail to click buttion : buttion_id=%s, URL=%s" % (buttion_id,), e=e)
            return False
        # alert : "대기예약이 완료 되었습니다"
        self.driver.implicitly_wait(10)
        time.sleep(2.5)
        try:
            alert = self.driver.switch_to.alert
            message = alert.text
            print("message : <%s>" % (message,))
            alert.accept()
            if "대기예약이 완료 되었습니다" not in message:
                return True
        except Exception as e:
            self.log("[Error] Fail to check alert", e=e) 
            return False
        return True


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
                _hh   = _hhmm.split(":")[0]
                _mm   = _hhmm.split(":")[1]
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
        form_uri="https://www.chinjucc.co.kr/Reservation/Reservation.aspx"
        next_javascript="javascript:moveCalendar(1);"
        yyyy = yyyymmdd[0:4]
        mm   = yyyymmdd[5:7]
        dd   = yyyymmdd[8:10]
        html = self.get_html(form_uri)
        while True:
            html = self.get_now_page()
            html_yyyy = html.split("년")[0].split(">")[-1]
            html_mm   = "%02d" % int(html.split("월")[0].split(">")[-1])
            #print("%s %s %s %s %s" % (yyyy, mm, dd, html_yyyy, html_mm))
            #print("%s %s %s html:%s %s" % (yyyy, mm, dd, html_yyyy, html_mm))
            if html_yyyy == yyyy and html_mm == mm:
                break
            try:
                self.run_javascript(next_javascript)
                self.driver.implicitly_wait(10)
            except:
                return False
            time.sleep(0.1)
        time.sleep(0.05)
        MAX_RETRY=10
        for idx in range(MAX_RETRY):
            try:
                html = self.get_now_page()
                break
            except:
                time.sleep(0.025)
                if idx == MAX_RETRY - 1:
                    self.log("[Error] !! max retry : 10")
                    return False
                continue
        # 해당일에 예약이 활성화 되있는지 찾음
        is_test = False
        if is_test == False:
            js_key = "javascript:GetTimeList('%s'" % yyyymmdd
            check_data = "%d일 : 예약마감" % int(dd)
            #print("%s" % check_data)
            if check_data in html:
                self.log("Error. Reservation already done")
                return "해당일은 이미 예약이 마감 되어 있습니다 (%s)" % yyyymmdd #None
            if js_key not in html:
                self.log("Error. Fail to found javascript : return False")
                return False
            reservation = html.split(js_key)[1].split(";")[0]
            reservation = "%s%s;" % (js_key, reservation)
            try:
                self.run_javascript(reservation)
            except:
                self.log("Error. Fail to call javascript : %s.. return False" % reservation)
                return False
            time.sleep(0.05)
            html = self.get_now_page()
        else:
            with open("./html2/ok.html", "rb") as fd:
                html = fd.read()
        ReserveSet = self.parser_reservation_time(html)
        if len(ReserveSet) == 0:
            self.log("Error. Fail to find ReserveSet : return False")
            return False



        except_list = []
        while True:
            item = self.select_reservation_time(ReserveSet, hope_1st, hope_2nd, cource_index)
            if item == None:
                self.log("Error. All item was sold out")
                return False
            except_list.append(item)

            MAX_RETRY = 4
            if is_test == False:
                for idx in range(MAX_RETRY):
                    try:
                        self.run_javascript(item['javascript'])
                        break
                    except Exception as e:
                        self.log("Error. 2 Fail to call javascript : %s.. retry" % item['javascript'])
                        time.sleep(0.25)
                        if idx == MAX_RETRY - 1:
                            self.log("Error. 2 Fail to call javascript : %s.. return False" % item['javascript'])
                            return False
                        continue
                time.sleep(0.25)
            else:
                print(item) # 테스트모드
                return True

            #self.driver.implicitly_wait(10)
            #time.sleep(1.5)
            try:
                alert = self.driver.switch_to.alert
                message = alert.text
                self.log("message : <%s>" % (message,))
                if "다른 분께서" in message:
                    alert.accept()
                    continue
            except Exception as e:
                self.log("[Error] Fail to check alert", e=e) 
            try:
                html = self.get_now_page()
            except common.exceptions.UnexpectedAlertPresentException as e:
                continue
            break
        html = html.split("\n")
        javascript = None
        javascript_list = []
        for idx, line in enumerate(html):
            if "예약하기" not in line or 'javascript:' not in line or 'ctl00_ContentPlaceHolder1_lbtOK' not in line:
                continue
            #<a onclick="if(!ReserveOK()) return false;" id="ctl00_ContentPlaceHolder1_lbtOK" href="javascript:["__doPostBack(\'ctl00$ContentPlaceHolder1$lbtOK\',\'\')", \'>예약하기</a>
            #javascript = "javascript:%s" % line.split('"')
            javascript = "javascript:__doPostBack(';ctl00$ContentPlaceHolder1$lbtOK';,';';)"
            javascript_list.append(javascript)
            javascript = "javascript:__doPostBack('ctl00$ContentPlaceHolder1$lbtOK','')"
            javascript_list.append(javascript)
            javascript = 'javascript:["__doPostBack(\'ctl00$ContentPlaceHolder1$lbtOK\',\'\')'
            javascript_list.append(javascript)
            break

        if javascript == None:
            self.log("Error. Fail found summit javascript in html page") 
            return False

        # 1. 예약하가 자바스크립트 실행
        f_ok = False
        for idx, javascript in enumerate(javascript_list):
            try:
                self.log("%d : %s" % (idx,javascript))
                self.run_javascript(javascript)
            except Exception as e:
                self.log("Error. Fail to call javascript : %s.. return False\n Error. %s" % (javascript, e))
                continue
            f_ok = True
            break
        if f_ok == False:
            self.log("Error. fail javascript all.. .retry return False")
            return False

        # 2. alart 예약하기 버튼 누르기
        try:
            alert = self.driver.switch_to.alert
            message = alert.text
            self.log("message1: %s" % (message,))
            alert.accept()
        except common.exceptions.NoAlertPresentException as e:
            self.log("11111 : NO alarm %s " % e)
            return False
        except common.exceptions.UnexpectedAlertPresentException as e:
            self.log("UnexpectedAlertPresentException 1 %s " % e)
            return False

        # 3. alart 예약완료 버튼 누르기
        try:
            alert = self.driver.switch_to.alert
            message = alert.text
            self.log("message2: %s" % (message,))
            alert.accept()
        except common.exceptions.NoAlertPresentException as e:
            self.log("11112 : NO alarm %s " % e)
            return False
        except common.exceptions.UnexpectedAlertPresentException as e:
            self.log("UnexpectedAlertPresentException 2 %s " % e)
            return False


        html = self.get_now_page()

        return True

def ChinjuccMain(input_param, log_fn, exit_check_fn):
    global g_log_fn
    global g_exit_check_fn
    g_log_fn = None
    g_exit_check_fn = None#exit_check_fn

    if platform.system() != "Windows":
        chromedriver = "./chromedriver"
    else:
        chromedriver = "chromedriver_86.0.4240.22.exe"
    
    try:
        bot = robotChinjucc(chromedriver, "chinjucc.co.kr")
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
                     "55b05110605658e51b66eafff7d28ce9", ]
       


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

    if bot.do_login(uid, pwd) == False:
        bot.log("Login fail!!")
        del bot
        return "로그인에 실패 하였습니다"
    bot.log("Login success!!")

    #bot.init_working_tab(day, 16)

    time.sleep(1)

    while True:
        try:
            if run_mode == 1:
                nErr = bot.do_reservation(day, hope_1st, hope_2nd, cource_index)
                if nErr == True:
                    break
                elif nErr == False:
                    pass
                else:
                    del bot
                    return nErr
            else:
                if bot.do_reservation_test(day, hope_1st, hope_2nd) != False:
                    break
            now = datetime.now()
            now_hhmm = now.hour * 100 + now.minute
            if now_hhmm < 850 or now_hhmm > 910:
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


