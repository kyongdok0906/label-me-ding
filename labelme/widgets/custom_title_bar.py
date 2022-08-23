from qtpy import QtCore, QtWidgets
from qtpy.QtWidgets import QGridLayout, QHBoxLayout, \
    QLabel, QLineEdit, QToolButton, QDockWidget, QStyle
from keyboard import press
from .. import utils


class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, objname, dockWG):
        super(CustomTitleBar, self).__init__()
        self.setObjectName(objname)
        self.setMaximumHeight(22)
        self.setContentsMargins(5, 0, 5, 2)
        # self.setStyleSheet("QWidget { border: 1px solid #aaa;} ")
        self._grades_dock = dockWG
        # setting UI
        self.initUI()

    def initUI(self):
        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(6)
        hbox_layout.setContentsMargins(0, 0, 0, 0)

        self.grades_lb = QLabel(self.tr("Grades (Total %s)" % 0))
        # self.grades_lb.setStyleSheet("QWidget { background-color: rgb(227, 227, 227); }")
        hbox_layout.addWidget(self.grades_lb, 0, QtCore.Qt.AlignLeft)

        tmp = QLabel()
        hbox_layout.addWidget(tmp, 1, QtCore.Qt.AlignLeft)

        self.grades_nw_lb = QLabel(self.tr("New Input"))
        self.grades_nw_lb.setMaximumWidth(70)

        self.grades_input_le = QLineEdit()
        self.grades_input_le.returnPressed.connect(self.new_input_grade_handle)
        self.grades_input_le.setMaximumWidth(120)

        self.minmaxbtn = QToolButton()
        # minmaxbtn.setIcon(utils.newIcon("box1"))
        self.minmaxbtn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarNormalButton")))
        self.minmaxbtn.setFixedSize(16, 16)
        self.minmaxbtn.clicked.connect(self.toggleActionEventHandle)
        self.minmaxbtn.setStyleSheet("QToolButton { border: 0; padding:3px } ")
        # self.minmaxbtn.setVisible(False)

        closebtn = QToolButton()
        # closebtn.setIcon(utils.newIcon("wx"))
        closebtn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton")))
        closebtn.setFixedSize(16, 16)
        closebtn.clicked.connect(self.closeActionEventHandle)
        closebtn.setStyleSheet("QToolButton { border: 0; padding:3px } ")
        # closebtn.setIconSize(QtCore.QSize(10, 10))
        # closebtn.setFixedSize(22, 22)
        # closebtn.setFocusPolicy(QtCore.Qt.ClickFocus)

        # closebtn.setStyleSheet("QToolButton:hover {border: 0; background-color: #e2fffd;} ")

        hbox_layout.addWidget(self.grades_nw_lb, 0, QtCore.Qt.AlignRight)
        hbox_layout.addWidget(self.grades_input_le, 0, QtCore.Qt.AlignRight)
        hbox_layout.addWidget(self.minmaxbtn, 0, QtCore.Qt.AlignRight)
        hbox_layout.addWidget(closebtn, 0, QtCore.Qt.AlignRight)
        # self.setStyleSheet("QWidget { border : 1px solid #aaa }")

        self.setLayout(hbox_layout)

    def setGradesCount(self, count: int):
        self.grades_lb.setText(self.tr("Grades (Total %s)" % count))

    def closeActionEventHandle(self):
        self._grades_dock.close()

    def toggleActionEventHandle(self):
        self._grades_dock.setFloating(True)

    def setKeyFocus(self):
        self.grades_input_le.setFocus()
        self.grades_input_le.setText(".")
        press('enter')
        #self.new_input_grade_handle()

    def new_input_grade_handle(self):
        input_str = self.grades_input_le.text()
        re_str = input_str.strip()
        if len(re_str) > 0:
            #print(re_str)
            _customlistwidget = self._grades_dock.widget()
            if _customlistwidget and len(_customlistwidget.grade_list) > 0:
                _customlistwidget.add_new_grade(re_str)

                if re_str == ".":
                    self.grades_input_le.setText("")
