from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle
from .. import utils
from labelme.widgets.custom_qlabel import CQLabel


class CustomListWidget(QtWidgets.QWidget):
    def __init__(self):
        self.selected_grade = None
        self.grade_list = []
        super(CustomListWidget, self).__init__()
        self.initUI()

    def initUI(self):

        self.HB_layout = QHBoxLayout()
        self.HB_layout.setContentsMargins(0, 0, 0, 0)
        self.HB_layout.setSpacing(0)
        items = [
            {
                "grade": "중량Bb"
            },
            {
                "grade": "경량AB"
            },
            {
                "grade": "생철LL"
            },
            {
                "grade": "경량AL"
            },
            {
                "grade": "선반C"
            },
            {
                "grade": "선반B"
            },
            {
                "grade": "슈레디드A"
            },
            {
                "grade": "슈레디드B"
            },
            {
                "grade": "길로틴A"
            },
            {
                "grade": "경량BL"
            },
            {
                "grade": "생철A"
            },
            {
                "grade": "중량A"
            },
            {
                "grade": "생압"
            },
            {
                "grade": "주물(모터블럭)"
            },
            {
                "grade": "경량B"
            },
            {
                "grade": "길로틴B"
            },
            {
                "grade": "압축B"
            },
            {
                "grade": "압축D"
            },
            {
                "grade": "선반A"
            },
            {
                "grade": "길로틴C"
            },
            {
                "grade": "중량BL"
            },
            {
                "grade": "압축A"
            },
            {
                "grade": "압축 E"
            },
            {
                "grade": "생철B"
            },
            {
                "grade": "중량AL"
            },
            {
                "grade": "경량C"
            },
            {
                "grade": "선반T"
            },
            {
                "grade": "슈레디드C"
            }
        ]
        item_count = len(items)
        done = False
        icount = 0
        for j in range(0, item_count):
            vbox = QVBoxLayout()
            vbox.setContentsMargins(6, 0, 6, 0)
            vbox.setSpacing(1)
            for i in range(4):
                if icount < item_count:
                    item = items[icount]
                    if item is not None:
                        qlb = CQLabel(item["grade"], self)
                        qlb.sizeHint()
                        qlb.setObjectName(item["grade"])
                        qlb.setStyleSheet("QWidget { border: 0px solid #aaa; font-size: 12px; }")
                        qlb.setMaximumWidth(100)
                        qlb.setFixedHeight(20)
                        vbox.addWidget(qlb)
                        self.grade_list.append(qlb)
                        icount = icount + 1
                else:
                    done = True
                    break
            if done is True:
                break
            else:
                qq = QtWidgets.QWidget()
                qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                qq.setLayout(vbox)
                self.HB_layout.addWidget(qq)

        twidget = QtWidgets.QWidget()
        twidget.setLayout(self.HB_layout)
        twidget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); }")
        scroll = QScrollArea()
        scroll.setWidget(twidget)
        scroll.setWidgetResizable(True)

        hb_layout = QHBoxLayout()
        hb_layout.addWidget(scroll)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        hb_layout.setSpacing(0)
        self.setLayout(hb_layout)

    def event_mouse_click(self):
        if len(self.grade_list) > 0:
            item_count = len(self.grade_list)
            for j in range(0, item_count):
                lbObj = self.grade_list.__getitem__(j)
                if lbObj is not None:
                    txt = lbObj.text()
                    objname = lbObj.objectName()  # will do using after this val
                    if txt != self.selected_grade:
                        lbObj.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0}")



class CustomListWidget_vvv(QtWidgets.QWidget):
    def __init__(self):
        self.selected_grade = None
        self.grade_list = []
        super(CustomListWidget_vvv, self).__init__()
        self.initUI()

    def initUI(self):

        self.HB_layout = QHBoxLayout()
        self.HB_layout.setContentsMargins(0, 0, 0, 0)
        self.HB_layout.setSpacing(0)
        items = [
            {
                "grade": "중량Bb"
            },
            {
                "grade": "경량AB"
            },
            {
                "grade": "생철LL"
            },
            {
                "grade": "경량AL"
            },
            {
                "grade": "선반C"
            },
            {
                "grade": "선반B"
            },
            {
                "grade": "슈레디드A"
            },
            {
                "grade": "슈레디드B"
            },
            {
                "grade": "길로틴A"
            },
            {
                "grade": "경량BL"
            },
            {
                "grade": "생철A"
            },
            {
                "grade": "중량A"
            },
            {
                "grade": "생압"
            },
            {
                "grade": "주물(모터블럭)"
            },
            {
                "grade": "경량B"
            },
            {
                "grade": "길로틴B"
            },
            {
                "grade": "압축B"
            },
            {
                "grade": "압축D"
            },
            {
                "grade": "선반A"
            },
            {
                "grade": "길로틴C"
            },
            {
                "grade": "중량BL"
            },
            {
                "grade": "압축A"
            },
            {
                "grade": "압축 E"
            },
            {
                "grade": "생철B"
            },
            {
                "grade": "중량AL"
            },
            {
                "grade": "경량C"
            },
            {
                "grade": "선반T"
            },
            {
                "grade": "슈레디드C"
            }
        ]
        item_count = len(items)
        done = False
        icount = 0
        for j in range(0, item_count):
            vbox = QVBoxLayout()
            vbox.setContentsMargins(6, 0, 6, 0)
            vbox.setSpacing(1)
            for i in range(4):
                if icount < item_count:
                    item = items[icount]
                    if item is not None:
                        qlb = CQLabel(item["grade"], self)
                        qlb.sizeHint()
                        qlb.setObjectName(item["grade"])
                        qlb.setStyleSheet("QWidget { border: 0px solid #aaa; font-size: 12px; }")
                        qlb.setMaximumWidth(100)
                        qlb.setFixedHeight(20)
                        vbox.addWidget(qlb)
                        #self.grade_list.append(qlb)
                        icount = icount + 1
                else:
                    done = True
                    break
            if done is True:
                break
            else:
                qq = QtWidgets.QWidget()
                qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                qq.setLayout(vbox)
                self.HB_layout.addWidget(qq)
        
        twidget = QtWidgets.QWidget()
        twidget.setLayout(self.HB_layout)
        twidget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); }")
        scroll = QScrollArea()
        scroll.setWidget(twidget)
        scroll.setWidgetResizable(True)

        hb_layout = QHBoxLayout()
        hb_layout.addWidget(scroll)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        hb_layout.setSpacing(0)
        self.setLayout(hb_layout)

    def drawLables(self, items, cond: str):
        if cond == "select_one" and len(self.grade_list) > 0:
            item_count = len(self.grade_list)
            for j in range(0, item_count):
                lbObj = self.grade_list.__getitem__(j)
                if lbObj is not None:
                    txt = lbObj.text()
                    objname = lbObj.objectName()  # will do using after this val
                    if txt != self.selected_grade:
                        lbObj.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0}")
        elif cond == "init" and len(items) > 0:
            hb_layout = QHBoxLayout()
            hb_layout.setContentsMargins(0, 0, 0, 0)
            hb_layout.setSpacing(0)

            item_count = len(items)
            done = False
            icount = 0
            for j in range(0, item_count):
                vbox = QVBoxLayout()
                vbox.setContentsMargins(6, 0, 6, 0)
                vbox.setSpacing(1)
                for i in range(4):
                    if icount < item_count:
                        item = items[icount]
                        if item is not None:
                            qlb = CQLabel(item["grade"], self)
                            qlb.sizeHint()
                            qlb.setObjectName(item["grade"])
                            qlb.setStyleSheet("QWidget { border: 0px solid #aaa; font-size: 12px; }")
                            qlb.setMaximumWidth(100)
                            qlb.setFixedHeight(20)
                            vbox.addWidget(qlb)
                            self.grade_list.append(qlb)
                            icount = icount + 1
                    else:
                        done = True
                        break
                if done is True:
                    break
                else:
                    qq = QtWidgets.QWidget()
                    qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                    qq.setLayout(vbox)
                    hb_layout.addWidget(qq)

            tmp_widget = QtWidgets.QWidget()
            tmp_widget.setLayout(hb_layout)
            tmp_widget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); }")
            # tmp_widget.setMinimumWidth(600)

            main_layout = QHBoxLayout()
            main_layout.addWidget(tmp_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            self.setLayout(main_layout)
        else:
            pass


# The code below is not used.
class CustomListWidget_v0(QtWidgets.QWidget):
    def __init__(self):
        super(CustomListWidget_v0, self).__init__()
        self.initUI()
        # print(self.height())
        self.selected_grade = None

    def initUI(self):

        self.HB_layout = QHBoxLayout()
        self.HB_layout.setContentsMargins(0, 0, 0, 0)
        self.HB_layout.setSpacing(0)
        items = [
            {
                "grade": "중량B"
            },
            {
                "grade": "경량A"
            },
            {
                "grade": "생철L"
            },
            {
                "grade": "경량AL"
            },
            {
                "grade": "선반C"
            },
            {
                "grade": "선반B"
            },
            {
                "grade": "슈레디드A"
            },
            {
                "grade": "슈레디드B"
            },
            {
                "grade": "길로틴A"
            },
            {
                "grade": "경량BL"
            },
            {
                "grade": "생철A"
            },
            {
                "grade": "중량A"
            },
            {
                "grade": "생압"
            },
            {
                "grade": "주물(모터블럭)"
            },
            {
                "grade": "경량B"
            },
            {
                "grade": "길로틴B"
            },
            {
                "grade": "압축B"
            },
            {
                "grade": "압축D"
            },
            {
                "grade": "선반A"
            },
            {
                "grade": "길로틴C"
            },
            {
                "grade": "중량BL"
            },
            {
                "grade": "압축A"
            },
            {
                "grade": "압축 E"
            },
            {
                "grade": "생철B"
            },
            {
                "grade": "중량AL"
            },
            {
                "grade": "경량C"
            },
            {
                "grade": "선반T"
            },
            {
                "grade": "슈레디드C"
            }
        ]
        item_count = len(items)
        done = False
        icount = 0
        for j in range(0, item_count):
            vbox = QVBoxLayout()
            vbox.setContentsMargins(6, 0, 6, 0)
            vbox.setSpacing(1)
            for i in range(4):
                if icount < item_count:
                    item = items[icount]
                    if item is not None:
                        qlb = CQLabel(item["grade"], self)
                        qlb.sizeHint()
                        # qlb.installEventFilter(self)
                        # QtCore.QObject.connect(qlb, QtCore.SIGNAL(_fromUtf8("clicked()")), self.grade_label_action)
                        # qlb.mouseReleaseEvent = self.mouseReleaseEventHandle
                        qlb.setObjectName(item["grade"])
                        qlb.setStyleSheet("QWidget { border: 0px solid #aaa; font-size: 12px; }")
                        qlb.setMaximumWidth(100)
                        qlb.setFixedHeight(20)
                        vbox.addWidget(qlb)
                        self.grade_list.append(qlb)
                        icount = icount + 1
                else:
                    done = True
                    break
            if done is True:
                break
            else:
                qq = QtWidgets.QWidget()
                qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                qq.setLayout(vbox)
                self.HB_layout.addWidget(qq)

        twidget = QtWidgets.QWidget()
        twidget.setLayout(self.HB_layout)
        twidget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); }")
        scroll = QScrollArea()
        scroll.setWidget(twidget)
        scroll.setWidgetResizable(True)

        hb_layout = QHBoxLayout()
        hb_layout.addWidget(scroll)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        hb_layout.setSpacing(0)
        self.grade_list = []
        self.setLayout(hb_layout)