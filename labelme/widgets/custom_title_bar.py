from qtpy import QtCore, QtWidgets
from qtpy.QtWidgets import QGridLayout, QHBoxLayout, \
    QLabel, QLineEdit, QToolButton, QDockWidget, QStyle
from keyboard import press
from .. import utils


class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, objname, parentDock):
        super(CustomTitleBar, self).__init__()
        self.setObjectName(objname)
        self.setMaximumHeight(22)
        self.setContentsMargins(5, 0, 5, 2)
        # self.setStyleSheet("QWidget { border: 1px solid #aaa;} ")
        self._parent_dock = parentDock
        # setting UI

        self.initUI()

    def initUI(self):
        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(6)
        hbox_layout.setContentsMargins(0, 0, 0, 0)

        if self.objectName() == "gradesbar":
            self.title_lb = QLabel(self.tr("Grades (Total %s)" % 0))
        elif self.objectName() == "productbar":
            self.title_lb = QLabel(self.tr("Product (Total %s)" % 0))
        # self.title_lb.setStyleSheet("QWidget { background-color: rgb(227, 227, 227); }")
        hbox_layout.addWidget(self.title_lb, 0, QtCore.Qt.AlignLeft)

        tmp = QLabel()
        hbox_layout.addWidget(tmp, 1, QtCore.Qt.AlignLeft)

        self.title_nw_lb = QLabel(self.tr("New Input"))
        self.title_nw_lb.setMaximumWidth(70)

        self.input_line_edit = QLineEdit()
        self.input_line_edit.returnPressed.connect(self.press_input_handle)
        self.input_line_edit.setMaximumWidth(120)

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

        hbox_layout.addWidget(self.title_nw_lb, 0, QtCore.Qt.AlignRight)
        hbox_layout.addWidget(self.input_line_edit, 0, QtCore.Qt.AlignRight)
        hbox_layout.addWidget(self.minmaxbtn, 0, QtCore.Qt.AlignRight)
        hbox_layout.addWidget(closebtn, 0, QtCore.Qt.AlignRight)
        # self.setStyleSheet("QWidget { border : 1px solid #aaa }")

        self.setLayout(hbox_layout)

    def setGradesCount(self, count: int):
        self.title_lb.setText(self.tr("Grades (Total %s)" % count))

    def closeActionEventHandle(self):
        self._parent_dock.close()

    def toggleActionEventHandle(self):
        self._parent_dock.setFloating(True)

    def pressEnterKeyForce(self):
        self.input_line_edit.setFocus()
        self.input_line_edit.setText("")
        press('enter')

    def press_input_handle(self):
        input_str = self.input_line_edit.text()
        re_str = input_str.strip()
        #if len(re_str) > 0:
            #print(re_str)
        _customlistwidget = self._parent_dock.widget()
        if _customlistwidget and len(_customlistwidget.items_list) > 0:
            _customlistwidget.addNewGrade(re_str)
            self.input_line_edit.setText("")
