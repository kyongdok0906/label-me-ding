import sys
import threading
import time

import requests, json
from PyQt5.QtWidgets import QDesktopWidget, QWidget
from qtpy import QtWidgets, QtCore
from labelme.utils.qt import LogPrint
from labelme.app import MainWindow
from labelme.utils.processini import *
from labelme.utils.qt import httpReq


class LoginDLG(QWidget):

    def __init__(
            self,
            config=None
    ):
        super().__init__()
        self._config = config
        self.initUI()

    def initUI(self):
        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(20, 20, 20, 10)
        grid.setVerticalSpacing(10)
        self.setLayout(grid)

        lb_id = QtWidgets.QLabel('ID *')
        grid.addWidget(lb_id, 0, 0, QtCore.Qt.AlignLeft)
        lb_id_edit = QtWidgets.QLineEdit()
        lb_id_edit.setFixedWidth(150)
        self._lb_id_edit=lb_id_edit
        grid.addWidget(lb_id_edit, 0, 1, QtCore.Qt.AlignLeft)

        lb_pwd = QtWidgets.QLabel('PWD *')
        grid.addWidget(lb_pwd, 1, 0, QtCore.Qt.AlignLeft)
        lb_pwd_edit = QtWidgets.QLineEdit()
        lb_pwd_edit.setFixedWidth(150)
        self._lb_pwd_edit = lb_pwd_edit
        grid.addWidget(lb_pwd_edit, 1, 1, QtCore.Qt.AlignLeft)

        lb_lang = QtWidgets.QLabel('Language ')
        grid.addWidget(lb_lang, 2, 0, QtCore.Qt.AlignLeft)

        cb = QtWidgets.QComboBox()
        cb.addItem('English', 'null')
        cb.addItem('Korean', 'ko_KR')
        # cb.addItem('Chinese', 'zh_CN')
        cb.setFixedWidth(100)
        # cb.activated[str].connect(self.onActivated)
        self._cb = cb
        grid.addWidget(cb, 2, 1, QtCore.Qt.AlignLeft)
        cbidx = 0
        for i in range(0, self._cb.count()):
            itxt = self._cb.itemData(i)
            ml = self._config["local_lang"]
            if itxt == ml:
                cbidx = i
                break

        self._cb.setCurrentIndex(cbidx)
        # self.cmb_second.addItem(self.cmb_Test.itemText(i))

        btn_login = QtWidgets.QPushButton('Login')
        btn_login.setFixedWidth(100)
        btn_login.clicked.connect(self.loginAction)
        grid.addWidget(btn_login, 3, 1, QtCore.Qt.AlignLeft)

        lb_alram = QtWidgets.QLabel('')
        lb_alram.setFixedWidth(200)
        lb_alram.setStyleSheet("QLabel { color : red; }")
        self._lb_alram = lb_alram
        grid.addWidget(lb_alram, 4, 1, QtCore.Qt.AlignLeft)

        self.setWindowTitle('Login Form')
        # self.setGeometry(300, 300, 200, 150)
        self.resize(200, 150)

        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # noinspection PyUnresolvedReferences
    def loginAction(self):
        # print("uname is " + self._lb_id_edit.text().strip())
        # print("pwd is " + self._lb_pwd_edit.text().strip())
        # print("cb  is " + self._cb.currentText() + " :: " + str(self._cb.currentData()))

        uid = self._lb_id_edit.text().strip()
        pwd = self._lb_pwd_edit.text().strip()
        lang = str(self._cb.currentData())
        self._config["local_lang"] = lang

        if not uid:
            self._lb_alram.setText("The ID should not be empty")
            threading.Timer(2, self.showErrorText).start()
            self._lb_id_edit.setFocus()
            return

        if not pwd:
            self._lb_alram.setText("The PWD should not be empty")
            threading.Timer(2, self.showErrorText).start()
            self._lb_pwd_edit.setFocus()
            return

        url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/login'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {'user_id': uid, 'password': pwd}
        # respone = requests.post(url, headers=headers, json=data)
        # jsstr = respone.json()
        jsstr = httpReq(url, "post", headers, data)
        # print(json.dumps(jsstr))
        if jsstr['message'] != 'success':
            # LogPrint(str("for login call server error").encode('utf-8'))
            self._lb_alram.setText("Invalid ID or PWD")
            threading.Timer(2, self.showErrorText).start()
        else:   # success
            if self._config is not None:
                self._config["grade_yn"] = "Y" if jsstr['grade_yn'].upper() == "Y" else "N"
                self._config["product_yn"] = "Y" if jsstr['product_yn'].upper() == "Y" else "N"
                self._config["label_yn"] = "Y" if jsstr['label_yn'].upper() == "Y" else "N"
                self._config["user_id"] = uid
            self._lb_alram.setText("Sucess Log in")
            self._config["login_state"] = True
            self.close()

    def showErrorText(self):
        self._lb_alram.setText("")
