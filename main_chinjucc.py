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
from site_chinjucc import *
from site_geojeviewcc import *


class MainWindowSite(MainWindow):
    def __init__(self):
        MainWindow.__init__(self)
        return

    def check_validation(self):
        param_dict = self._build_form_params()
        if param_dict["QTextEdit"]["아이디"] == "":
            self._message_box("'아이디'에 사이트 ID를 입력하세요")
            return False
        if param_dict["QTextEdit"]["비밀번호"] == "":
            self._message_box("'비밀번호'에 사이트 Password를 입력하세요")
            return False
        input_date = param_dict["QTextEdit"]["날짜"]
        if input_date == "":
            self._message_box("날짜에 예약할 일자를 입력하세요")
            return False
        matches = re.search(r'^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$', input_date)
        if matches == None:
            self._message_box("휴효하지 않은 날짜 형식")
            return False
        now = datetime.now()
        endtime = now+timedelta(days=60)
        nowDate = int(now.strftime('%Y%m%d'))
        endDate = int(endtime.strftime('%Y%m%d'))
        input_date = int(input_date.replace("-", ""))
        if nowDate >= input_date or endDate < input_date:
            self._message_box("익일부터 60일 이내의 날짜를 입력하세요")
            return False

        hope_1st = check_time_validation(param_dict["QTextEdit"]["희망시간1"])
        hope_2nd = check_time_validation(param_dict["QTextEdit"]["희망시간2"])
        if hope_1st == None:
            self._message_box("올바른 희망시간을 입력하세요 : eg. 09:35")
            return False
        if param_dict["QTextEdit"]["희망시간2"] != "":
            if hope_2nd == None:
                self._message_box("올바른 희망시간2를 입력하세요 : eg. 09:35")
                return False
        return True




def run_muilti_browser_proc(input_param, botObject, delete):
    input_param = copy.deepcopy(input_param)
    base_time = input_param["QTextEdit"]["희망시간1"]
    hh = int(base_time[0:2])
    mm = int(base_time[3:5])
    secs = hh * 3600 + mm * 60
    secs += (delete * 60)
    base_time = "%02d:%02d" % (secs // 3600, ((secs % 3600)//60))
    input_param["QTextEdit"]["희망시간1"] = base_time

    print("!!!! : %s" % base_time)
    
    hThread = threading.Thread(target=botObject, args=(input_param, None, None))
    hThread.daemon = True
    hThread.start()

def WinMain(botObject):
    app = QApplication(sys.argv)
    while True:
        win = MainWindowSite()
        win.add_login_form()
        win.add_calendar()
        win.add_edit_line("희망시간1")
        win.add_edit_line("희망시간2")
        win.add_edit_line("동시시도")
        win.add_edit_line("시간간격")
        win.add_comdobox("장소선택", ["진주CC", "거제뷰CC"])
        win.add_comdobox("코스선택", ["남강/해돋이", "촉석/해넘이"])
        win.add_comdobox("모드선택", ["실전모드", "테스트모드"])
        win.add_summit_buttion()
        win.initUI(title=" 컨트리클럽 자동예약 <2021-02-06>")
        win.show()
        app.exec_()

        input_param = win.get_param_dict()
        if input_param == None:
            break

        hope_time1 = input_param["QTextEdit"]["희망시간1"]
        hope_time2 = input_param["QTextEdit"]["희망시간1"]
        if (len(hope_time1) < 5 and ":" in hope_time1) or (len(hope_time2) < 5 and ":" in hope_time2):
            input_param["QTextEdit"]["희망시간1"] = "%02d:%02d" % (int(hope_time1.split(":")[0]), int((hope_time1.split(":")[0])))
            input_param["QTextEdit"]["희망시간2"] = "%02d:%02d" % (int(hope_time2.split(":")[0]), int((hope_time2.split(":")[0])))

        try:
            n_runn_chrome = int(input_param["QTextEdit"]["동시시도"])
            n_time_interval = int(input_param["QTextEdit"]["시간간격"])
        except:
            n_runn_chrome = 1
        n_runn_chrome -= 1
        n_run = 0

        print(input_param["QComboBox"]["장소선택"])
        if input_param["QComboBox"]["장소선택"] == 1:
            botObject = GeojeViewccMain

        for idx in range(int(n_runn_chrome/2) + 1):
            run_muilti_browser_proc(input_param, botObject, ((idx+1) * n_time_interval) *  1)
            n_run += 1
            if n_run < n_runn_chrome:
                run_muilti_browser_proc(input_param, botObject, ((idx+1) * n_time_interval) * -1)
        nErr = botObject(input_param, None, None)
        if nErr != True:
            error_str = "%s" % (nErr,)
            win.message_box(error_str)
        break
    sys.exit()


# hope_time     : hh:mm
# course        : 1=남강코스, 2=촉석코스

if __name__ == "__main__":
    WinMain(ChinjuccMain)

