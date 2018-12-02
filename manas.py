import os
import sys
import time
import threading
import urllib.request
import logging.handlers
import gevent
import manasM
from ctypes import windll, CFUNCTYPE, c_int, POINTER, c_void_p
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QComboBox, QWidget, QApplication, QMouseEventTransition
from PyQt5.QtCore import *
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from gevent.pool import Pool
from gevent.queue import Queue

user32 = windll.user32
kernel32 = windll.kernel32

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202


WH_KEYBOARD_LL = 13
WH_MOUSE = 7
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
CTRL_CODE = 162


Ui_Widget, _ = uic.loadUiType("mana.ui")

log = logging.getLogger('manas_log')
log.setLevel(logging.DEBUG)

formatter1 = logging.Formatter('[%(levelname)s]┃%(filename)s:%(lineno)d┃%(message)s┃')
formatter2 = logging.Formatter('┃%(message)s┃')

fileHandler = logging.FileHandler('./log.txt')
streamHandler = logging.StreamHandler()

fileHandler.setFormatter(formatter2)
streamHandler.setFormatter(formatter1)

log.addHandler(fileHandler)
log.addHandler(streamHandler)

options = webdriver.ChromeOptions()
# options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/61.0.3163.100 Safari/537.36")
options.add_argument("lang=ko_KR")  # 한국어!


# self.combo.setStyleSheet(":hover {border-bottom-right-radius: 3px;}")
is_LeftClickDown = False
# TODO 훅함수
def getFPTR(fn):
    CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
    return CMPFUNC(fn)

def hookProc(nCode, wParam, lParam):
    global is_LeftClickDown
    if WM_LBUTTONDOWN == wParam:
        is_LeftClickDown = True
    elif WM_LBUTTONUP == wParam:
        is_LeftClickDown = False
        keyhook.is_combo = False
    return user32.CallNextHookEx(keyhook.hooked, nCode, wParam, lParam)

# TODO 폼


class Form(QWidget, Ui_Widget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent=parent)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.combo.installEventFilter(self)
        self.combo_2.installEventFilter(self)
        self.highPath = ""  # 최상위 경로
        self.urlList = []  # 주소
        self.soup = {}  # 뷰티플수프
        self.path = ""  # 중간 경로

        self.pool = Pool(4)
        self.drivers = webdriver.Chrome('./chromedriver', chrome_options=options)  # 크롬드라이버위치 지정및 옵션 설정
        self.drivers.get("http://manazero008h.blogspot.com/2015/08/150_9.html")
        self.flag("리스트")
        self.comboIndex = 0
        self.ex = 0  # - event x좌표
        self.ey = 0  # - event y좌표
        self.originalName = ""
        self.d_t = []
        self.i_t = []
        self.masterD = []
        self.is_Tag = False  # 태그존재유무
        self.is_Url = False  # 주소 체크
        self.is_LoadFile = False  # 파일읽기 링크읽기
        self.combotext = self.combo.itemText(self.combo.currentIndex())
        settings = QSettings()
        self.lineEdit_2.setText(settings.value("userDir", None, type=str))
        self.User32 = user32
        self.hooked = None
        self.is_combo = False

# TODO 훅설치

    def installHookProc(self, pointer):
        self.hooked = self.User32.SetWindowsHookExA(WH_MOUSE_LL, pointer, kernel32.GetModuleHandleW(None), 0)
        if not self.hooked:
            return False
        return True

# TODO 훅제거

    def uninstallHookProc(self):
        if self.hooked is None:
            return
        print("훅 제거")
        self.User32.UnhookWindowsHookEx(self.hooked)


    def tag_check(self, flag):  # 현재페이지에 해당 태그가 존재하는지 유무 체크
        global m
        m = manasM.Module()
        self.is_Tag = False  # 태그존재유무
        self.soup = bs(self.drivers.page_source, 'html.parser')  # 현재 웹페이지를 soup로 보기좋게 바꿔준다.
        if self.drivers.title == "콘텐츠 경고":
            self.drivers.find_element_by_xpath('//*[@id="maia-main"]/p[2]/a[1]').click()
            return
        if flag == "제목":
            a = self.soup.select("#Blog1 > div.blog-posts.hfeed > div > div > div > div > h3")
            if len(a) != 0:
                self.originalName = a[0].text.strip()
                self.path = "/" + m.text_reg(self.originalName) + "/"
                log.debug("현재 경로 = " + self.highPath + self.path)
                self.is_Tag = True  # 태그존재유무
        elif flag == "페이지":
            b = self.soup.select("div > div.adsbygoogle")
            if len(b) != 0:
                self.is_Tag = True  # 태그존재유무
        elif flag == "리스트":
            c = self.soup.select('#HTML1 > div.widget-content > div > div > span > div > span a')
            if len(c) != 0:
                self.is_Tag = True
                for i, aa in enumerate(c):
                    if 0 < i <= 33:  # 0보다 i가 크면서 i가 33 이랑 작거나 같을때까지
                        #  print(str(i) + " " + str(c[i].attrs['href']))
                        self.combo.addItem(c[i].text, c[i].attrs['href'])
                self.combo.addItem("최신", "http://manazero008h.blogspot.com/2015/08/150_9.html")
        elif flag == "퍼스트":
            d = self.soup.select('div[id*=post] > div.related-posts-widget > ul > li > a[href]')
            self.masterD = d
            if len(d) != 0:
                self.is_Tag = True
                self.path = "/"
                self.originalName = ""
                self.combo_2.addItem(self.combo.itemText(self.combo.currentIndex()) + "목록", "목록")
                for i, v in enumerate(d):
                    self.combo_2.addItem(d[i].text, d[i].attrs['href'])

    def flag(self, flag):
        while True:
            self.tag_check(flag)
            if self.is_Tag is True:
                break

    @pyqtSlot()
    def select_item(self):
        self.combo_2.clear()
        t2 = threading.Thread(target=self.select_start)
        t2.daemon = True
        t2.start()

    def select_start(self):
        self.msg_thread("목록 불러오는중...")
        self.drivers.get(self.combo.itemData(self.combo.currentIndex()))
        self.flag("퍼스트")
        self.msg_thread("불러오기완료")

    @pyqtSlot()
    def win_min(self):
        self.showMinimized()

    @pyqtSlot()
    def gui_close(self):
        log.debug("구이 : 드라이버 종료")
        self.hide()
        self.pool.kill()
        self.drivers.quit
        keyhook.uninstallHookProc()
        sys.exit(app.exit())

    @pyqtSlot()
    def file_load_check(self):
        if self.radioButton.isChecked() is True:
            self.is_LoadFile = True  # 파일읽기 링크읽기
            self.radioButton.setText("파일 읽기")
            log.debug("텍스트")
        else:
            self.is_LoadFile = False  # 파일읽기 링크읽기
            self.radioButton.setText("링크 읽기")
            log.debug("링크")

    @pyqtSlot()
    def set_url(self):
        settings = QSettings()
        settings.setValue("userUrl", self.lineEdit.text())
        settings.sync()
        log.debug("입력 받은 주소 = " + self.lineEdit.text())

    @pyqtSlot()
    def set_dir(self):
        self.highPath = self.lineEdit_2.text()
        settings = QSettings()
        settings.setValue("userDir", self.lineEdit_2.text())
        settings.sync()
        log.debug("입력 받은 경로 = " + self.highPath)

    def msg_thread(self, msg, flag=0):
        def msg_set(ms, mf):
            self.msg.setText(ms)
            if mf == 0:  # 0일때만 1초뒤에 감쳐준다.
                time.sleep(1)
                self.msg.setText("")

        msg_set(msg, flag)
# TODO 다운버튼
    @pyqtSlot()
    def mana_down(self):
        t1 = threading.Thread(target=self.download)
        t1.daemon = True
        t1.start()

    def download(self):
        log.debug("┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃ 시 작 ┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃")

        def set_url_list():
            self.msg_thread("주소 체크중", 1)
            self.urlList = []  # 주소 초기화
            if self.is_LoadFile is True:  # 현재 파일 읽기가 체크된 경우
                f = open("./주소.txt", 'r')  # 주소.txt를 읽어들인다.
                self.urlList = f.readlines()  # 읽은 주소의 내용을 라인단위 배열로 바꿔서 self.urlList에 담는다.
                f.close()  # f객체를 닫아준다.
            else:  # 현재 링크 읽기가 체크된 경우
                self.urlList = [self.combo_2.itemData(self.combo_2.currentIndex())]  # 입력받은 주소를 담아준다.
            log.debug("셋팅된 URL = " + str(self.urlList))

        set_url_list()
        # print("현재 콤보 텍스트 = " + self.combotext)
        for url in self.urlList:
            div = []
            if self.combotext != "최신":
                try:
                    self.drivers.get(url)  # 여기가 처음 드라이버 겟 하는곳
                    self.is_Url = True  # 주소 체크
                except Exception:
                    self.is_Url = False  # 주소 체크
                    self.msg_thread("manazero 주소가 아닙니다.")
                self.flag("제목")  # 제목이 존재하는지
                self.msg_thread("주소가 유효 합니다.")
                h2 = self.soup.select('div[id*=post] > div.related-posts-widget h2')
                div = self.soup.select('div[id*=post] > div.related-posts-widget')[len(h2) - 1].select(
                    'ul > li > a[href]')
                div.reverse()  # 뒤집어준다.
            else:
                div = [self.masterD[self.combo_2.currentIndex()]]
            # print(div)
            self.msg_thread(self.originalName, 1)
            for div_i, div_a in enumerate(div):  # 해당 페이지의 모든 글링크

                log.debug("서브 주소 = " + div_a.attrs['href'])
                if div_i == 0:
                    self.drivers.get(div_a.attrs['href'])
                self.flag("페이지")  # 해당 태그 존재하는지
                self.soup = bs(self.drivers.page_source, 'html.parser')  # 현재 웹페이지를 soup로 보기좋게 바꿔준다.
                if self.combo.itemText(self.combo.currentIndex()) != "최신":
                    try:
                        self.d_t = [gevent.spawn(self.drivers.get, div[div_i + 1].attrs['href'])]  # 미리 다음페이지로 이동한다.
                    except Exception:
                        pass
                img = self.soup.select('h3 > div > div.adsbygoogle > div a[href]')  # 모든 이미지 링크들
                #     # 파일 다운로드 (주소,경로)
                log.debug("")
                log.debug(m.text_reg(div_a.text) + "               start")
                if not os.path.isdir(self.highPath + self.path):
                    os.mkdir(self.highPath + self.path)
                if not os.path.isdir(self.highPath + self.path + m.text_reg(div_a.text)):
                    os.mkdir(self.highPath + self.path + m.text_reg(div_a.text))

                imgsI = Queue()
                imgsA = Queue()

                def test_queue_get(n):
                    while not imgsA.empty():
                        imgI = imgsI.get_nowait()
                        imgA = imgsA.get_nowait()
                        dir = self.highPath + self.path + m.text_reg(div_a.text) + "/" + str(
                            div_i + 1) + "_" + str(imgI + 1) + ".png"  # 경로
                        if not os.path.isfile(dir):
                            gevent.joinall([gevent.spawn(urllib.request.urlretrieve, imgA.attrs['href'], dir)])  # 비동기로 다운로드를 하면서 기다린다
                            log.debug(str(n) + " " + str(len(self.pool)) + self.originalName + "[" + str(
                                div_i + 1) + "_" + str(imgI + 1) + "] = " + str(imgA.attrs['href']))

                def test_queue_set(img):
                    for img_i, img_a in enumerate(img):
                        imgsI.put_nowait(img_i)
                        imgsA.put_nowait(img_a)

                gevent.spawn(test_queue_set, img).join()
                self.pool.map(test_queue_get, range(4))

                # gevent.joinall([
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                #     gevent.spawn(test_queue_get),
                # ])
                if self.combo.itemText(self.combo.currentIndex()) != "최신":
                    gevent.joinall(self.d_t)

                log.debug(m.text_reg(div_a.text) + "               end")
                log.debug("")
        log.debug("┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃ 모 두 완 료 ┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃")

        self.msg_thread("다운로드완료", )
# TODO 마우스눌림 이벤트
    def mousePressEvent(self, event):  # 마우스 눌림인지 체크하는 기본함수
        # print("클릭됨")
        self.ex = - event.x()
        self.ey = - event.y()
# TODO 마우스무브 이벤트
    def mouseMoveEvent(self, event):  # 실시간 마우스 좌표가져오는 기본함수
        global is_LeftClickDown
        print(is_LeftClickDown)
        def xy(xy):
            return lambda x: x + xy

        # print(self.underMouse())
        x = xy(event.globalX())
        y = xy(event.globalY())
        # print("mx = {0} my = {1} x = {2} y = {3}".format(mx, my, x, y))
        if not self.is_combo:
            self.move(x(self.ex), y(self.ey))
        # txt = "Mouse 위치 ; x={0},y={1}, global={2},{3}".format(event.x(), event.y(), event.globalX(), event.globalY())
        # print(txt)
        # print(event.MouseButtonPress)
# TODO 클로즈 이벤트
    def closeEvent(self, event):  # 닫기를 실시간 감지하는 기본함수
        log.debug("┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃ 종 료 ┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃")
        log.debug("드라이버 종료")
        keyhook.uninstallHookProc()
        self.drivers.quit()
        self.pool.kill()
        self.deleteLater()

# TODO 이벤트 필터
    def eventFilter(self, obj, event):
        if event.type() == 10:
            if obj == self.combo or obj == self.combo_2:
                self.is_combo = True

        return super(Form, self).eventFilter(obj, event)

    #
    # def enterEvent(self, event):
    #
    #     if self.combo.underMouse():
    #         self.combo.underMouse()
    #         print("현재 마우스는 콤보안에 있어")
    #     return super(Form, self).enterEvent(event)
    # def leaveEvent(self, event):
    #     print("Mouse Left")
    #     return super(Form, self).enterEvent(event)

    # def mouseReleaseEvent(self, event):
    #     pass


if __name__ == '__main__':
    print("시작중...")
    QCoreApplication.setApplicationName("mana")
    QCoreApplication.setOrganizationDomain("manas")
    app = QApplication(sys.argv)
    f = Form()
    keyhook = f
    pointer = getFPTR(hookProc)
    if keyhook.installHookProc(pointer):
        print("훅설치")
    f.show()
    sys.exit(app.exec_())
