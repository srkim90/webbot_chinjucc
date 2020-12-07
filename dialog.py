import os
import sys
import copy
import json
import base64
import threading
from datetime import datetime
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPalette
#from SubWindow import SubWindow

class ProgressWindow(QMainWindow):
    def __init__(self, input_param, botObject):
        QMainWindow.__init__(self)
        x_size=500
        y_size=700
        y_now=0
        self.log_idx = 0
        self.log_queue = []
        self.async_lock = threading.Semaphore(1)

        self.input_param = input_param
        self.botObject = botObject

        movie_size = 150
        self.setWindowTitle("웹봇 실행중")
        self.setGeometry(10, 10, x_size, y_size)
        self.logViewer = QListWidget(self)
        self.logViewer.resize(x_size - 20, x_size - 20)
        self.logViewer.move(10,10)
        self.logViewer.scrollToBottom()


        y_now = x_size - 20

        self.moviee = QLabel(self)
        self.movie = QMovie("DOING.gif")
        self.movie.setScaledSize(QSize(movie_size, movie_size))
        self.movie.start()
        self.moviee.setMovie(self.movie)
        self.moviee.move(x_size/2-movie_size/2, y_now + 20)
        y_now += int(movie_size) + 30

        pal = QPalette()
        pal.setColor(QPalette.Background, QColor(253, 253, 254))
        self.setPalette(pal)

        self.button = QPushButton("중단", self)
        self.button.resize(x_size - 20, 20)
        self.button.move(10, y_now)
        self.button.clicked.connect(self.clickMethod)


        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.timeout)
        self.timer.start()

        self.n_click_btn=0
        self.center()

        self.hThread = threading.Thread(target=self.webRobot_thread, args=(input_param, botObject,))
        self.hThread.daemon = True
        self.hThread.start()

    def get_status(self):
        return self.n_click_btn

    def webRobot_thread(self, input_param, botObject):
        botObject(input_param, self.add_log, self.get_status)
        self.clickMethod()

    def add_log(self, log_string, log_level=0):
        log_info = {
                    "log_string" : log_string,
                    "log_level"  : log_level,
                }
        self.async_lock.acquire()
        self.log_queue.append(log_info)
        self.async_lock.release()

    def timeout(self):
        log_queue = None
        self.async_lock.acquire()
        if len(self.log_queue) != 0:
            log_queue = self.log_queue[0:]
            self.log_queue = []
        self.async_lock.release()
        if log_queue != None:
            for log_info in log_queue:
                log_string = log_info["log_string"]
                log_level = log_info["log_level"]
                self.__add_log(log_string, log_level)
        return

    def __add_log(self, log_string, log_level=0):
        LOG_COLOR_DBG='#7fc97f'
        LOG_COLOR_INF='#ffff99'
        LOG_COLOR_CRT='#f0027f'
        LOG_COLOR_ERR='#666666'
        if log_level == 0:
            now_color=LOG_COLOR_DBG
        elif log_level == 1:
            now_color=LOG_COLOR_INF
        elif log_level == 2:
            now_color=LOG_COLOR_CRT
        else:
            now_color=LOG_COLOR_ERR
        now = datetime.now()
        now_time = "%s-%02d-%02d %02d:%02d:%02d" %(now.year, now.month, now.day, now.hour, now.minute, now.second)
        new_string = "[%02d] %s --> %s" % (self.log_idx, now_time, log_string)
        item = QListWidgetItem(new_string)
        item.setBackground(QColor(now_color))
        self.logViewer.addItem(item)
        self.logViewer.scrollToBottom()
        self.log_idx += 1

    def clickMethod(self):
        if self.n_click_btn == 0:
            self.setWindowTitle("웹봇 중단됨")
            self.button.setText("종료")
            self.n_click_btn += 1
            self.movie.stop()
        else:
            self.close()
        #self.n_click_btn += 1

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(10, 10)
        self.move(qr.topLeft())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.edit_dict={}
        self.combobox_dict={}
        self.x_base=20
        self.y_base=20
        self.edit_line_x=240
        self.label_line_x=70
        self.edit_line_y=25
        self.edit_space=3
        self.button=None
        self.param_dict = None

    def get_param_dict(self):
        return self.param_dict

    def add_comdobox(self, form_name, item_list):
        x_base = self.x_base
        label = QLabel(self)
        label.move(x_base, self.y_base)
        label.resize(self.label_line_x, self.edit_line_y)
        font = label.font()
        font.setPointSize(10)
        font.setFamily("Courier New");
        label.setFont(font)
        form_label_text = "%s" % form_name
        label.setText(form_label_text)
        x_base += self.label_line_x + self.edit_space
        qb = QComboBox(self)
        for item in item_list:
            qb.addItem(item)
        form_lbx = QBoxLayout(QBoxLayout.TopToBottom, parent=self)
        self.setLayout(form_lbx)
        qb.move(x_base, self.y_base)
        qb.resize(self.edit_line_x, self.edit_line_y)
        form_lbx.addWidget(qb)
        self.combobox_dict[form_name] = qb
        self.y_base += self.edit_line_y + self.edit_space
        return self.combobox_dict[form_name]



    def add_calendar(self, name="calendar"):
        form = self.add_edit_line("날짜")
        form.resize(self.edit_line_x - 45, self.edit_line_y)
        self.button = QPushButton("달력", self)
        self.button.resize(42, self.edit_line_y)
        self.button.move(self.x_base + self.edit_line_x + 30, self.y_base - self.edit_line_y - self.edit_space)
        self.button.clicked.connect(self.CalendarClickMethod)
        return

    def CalendarClickMethod(self):
        self.dateWindow = QWidget()
        self.cal = QCalendarWidget(self)
        self.cal.clicked[QDate].connect(self.showDate)
        #self.cal.move(self.x_base, self.y_base)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.cal)
        self.dateWindow.setLayout(self.hbox)
        self.dateWindow.setGeometry(300, 300, 350, 300)
        self.dateWindow.setWindowTitle('Calendar')
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.dateWindow.move(qr.topLeft())
        self.dateWindow.show()

        width = self.cal.frameGeometry().width()
        height = self.cal.frameGeometry().height()
        self.y_base += height + 600

    def showDate(self):
        #print ("Date picked: ", self.cal.selectedDate())
        yyyy = self.cal.selectedDate().year()
        mm   = self.cal.selectedDate().month()
        dd   = self.cal.selectedDate().day()
        self.edit_dict["날짜"].setText("%d-%02d-%02d" % (yyyy,mm,dd))
        self.dateWindow.close()

    def add_edit_line(self, form_name, baseClass=QTextEdit):
        x_base = self.x_base
        label = QLabel(self)
        label.move(x_base, self.y_base)
        label.resize(self.label_line_x, self.edit_line_y)
        font = label.font()
        font.setPointSize(10)
        font.setFamily("Courier New");
        label.setFont(font)
        form_label_text = "%s" % form_name
        label.setText(form_label_text)
        x_base += self.label_line_x + self.edit_space
        edit = baseClass(self)
        edit.move(x_base, self.y_base)
        edit.resize(self.edit_line_x, self.edit_line_y)
        if baseClass==QTextEdit:
            edit.setTabChangesFocus(True)
        self.edit_dict[form_name] = edit
        self.y_base += self.edit_line_y + self.edit_space
        return self.edit_dict[form_name]

    def add_input_form(self, form_name, n_line=1, show_title=True, baseClass=QLineEdit):
        x_base = self.x_base
        label = QLabel(self)
        label.move(x_base, self.y_base)
        label.resize(self.label_line_x, self.edit_line_y)
        font = label.font()
        font.setPointSize(10)
        font.setFamily("Courier New");
        label.setFont(font)
        form_label_text = form_name
        label.setText(form_label_text)
        edit = baseClass(self)
        self.y_base += 20
        edit.move(x_base, self.y_base)
        edit.resize(self.edit_line_x + self.label_line_x + self.edit_space, self.edit_line_y * n_line)
        edit.setTabChangesFocus(True)
        self.edit_dict[form_name] = edit
        self.y_base += self.edit_line_y + self.edit_space

    def add_login_form(self):
        edit = self.add_edit_line("아이디")
        edit = self.add_edit_line("비밀번호", baseClass=QLineEdit)
        edit.setEchoMode(QLineEdit.Password)

    def add_summit_buttion(self):
        self.button = QPushButton("시작", self)
        self.button.resize(self.edit_line_x + self.label_line_x + self.edit_space, self.edit_line_y)
        self.button.move(self.x_base, self.y_base)
        self.y_base += self.edit_line_y + self.edit_space
        #self.button.setTabChangesFocus(True)
        self.button.clicked.connect(self.clickMethod)

    def check_validation(self):
        return True

    def message_box(self, msg_string, detail_string=None ):
        self._message_box(msg_string, detail_string)

    def _message_box(self, msg_string, detail_string=None ):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(msg_string)
        msg.setWindowTitle("Web robot message")
        if detail_string != None:
            msg.setDetailedText(detail_string)
        retval = msg.exec_()

    def _build_form_params(self):
        param_dict = {
                "QTextEdit" : {
                    },
                "QComboBox" : {
                    },
                }
        for item in self.edit_dict.keys():
            if type(self.edit_dict[item]) == QLineEdit:
                value=self.edit_dict[item].text()
            else:
                value=self.edit_dict[item].toPlainText()
            param_dict["QTextEdit"][item] = value
        for item in self.combobox_dict.keys():
            value = self.combobox_dict[item].currentIndex()
            param_dict["QComboBox"][item] = value
        return param_dict    
    
    def clickMethod(self):
        if self.check_validation() == False:
            return
        self.param_dict = self._build_form_params()
        param_dict = copy.deepcopy(self.param_dict)
        try:
            param_dict["QTextEdit"]["비밀번호"] = ""
            param_dict["QComboBox"]["모드선택"] = 0
        except KeyError as e:
            pass
        json_input = json.dumps(param_dict).encode("utf-8")
        b64_json = base64.b64encode(json_input)
        with open(".metadata.dat", "wb") as fd:
            fd.write(b64_json)
        self.close()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(10, 10)
        self.move(qr.topLeft())

    def initUI(self, title="Web Robot"):
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowTitle(title)
        self.setGeometry(100, 100, self.x_base * 2 + self.edit_line_x + self.label_line_x + self.edit_space, self.y_base + 20)
        self.center()
 
        if os.path.exists(".metadata.dat") == True:
            with open(".metadata.dat", "rb") as fd:
                b64_json = fd.read()
                json_input = base64.b64decode(b64_json)
                param_dict = json.loads(json_input)
                for item in param_dict["QTextEdit"]:
                    value = param_dict["QTextEdit"][item]
                    for item2 in self.edit_dict.keys():
                        if item2 == item:
                            self.edit_dict[item].setText(value)
                if "QComboBox" in param_dict.keys():
                    for item in param_dict["QComboBox"]:
                        value = param_dict["QComboBox"][item]
                        for item2 in self.combobox_dict.keys():
                            if item2 == item:
                                self.combobox_dict[item].setCurrentIndex(value)
                if self.edit_dict["동시시도"].toPlainText() == "":
                    self.edit_dict["동시시도"].setText("8")
                if self.edit_dict["시간간격"].toPlainText() == "":
                    self.edit_dict["시간간격"].setText("5")
    def show(self):
        super().show()

'''
def WinMain(botObject):
    app = QApplication(sys.argv)
    while True:
        win = MainWindow()
        win.add_login_form()
        win.add_summit_buttion()
        win.initUI()
        win.show()
        app.exec_()

        input_param = win.get_param_dict()
        if input_param == None:
            break

        win = ProgressWindow(input_param, botObject)
        win.show()
        app.exec_()
    sys.exit()
'''
