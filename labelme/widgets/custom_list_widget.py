from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle
from .. import utils
from labelme.widgets.custom_qlabel import CQLabel


class CustomListWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        self.selected_grade = None
        self.grade_list = []
        self._parent = parent
        super(CustomListWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):

        self.HB_layout = QHBoxLayout(self._parent)
        self.HB_layout.setContentsMargins(6, 6, 6, 6)
        self.HB_layout.setSpacing(0)
        self.HB_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.HB_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        """
        items = [
            {
                "grade": "하나"
            },
            {
                "grade": "둘"
            },
            {
                "grade": "셋"
            },
            {
                "grade": "넷"
            },
            {
                "grade": "다섯입니다"
            }
        ]
        item_count = len(items)
        done = False
        icount = 0
        for j in range(0, item_count):
            vbox = QVBoxLayout()
            vbox.setContentsMargins(6, 0, 6, 0)
            vbox.setSpacing(1)
            vbox.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
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
                vc = vbox.count()
                if vc > 0:
                    qq = QtWidgets.QWidget()
                    qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                    qq.setLayout(vbox)
                    qq.setMaximumWidth(102)
                    self.HB_layout.addWidget(qq)
                break
            else:
                qq = QtWidgets.QWidget()
                qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                qq.setLayout(vbox)
                qq.setMaximumWidth(102)
                self.HB_layout.addWidget(qq)
        """

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
                        lbObj.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")

    def addItemsToQHBox(self, items):
        if len(items) > 0:
            self.grade_list.clear()
            item_count = len(items)
            done = False
            icount = 0
            for j in range(0, item_count):
                vbox = QVBoxLayout()
                vbox.setContentsMargins(1, 0, 2, 0)
                vbox.setSpacing(2)
                #vbox.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)
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
                    vc = vbox.count()
                    if vc > 0:
                        qq = QtWidgets.QWidget()
                        qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                        qq.setLayout(vbox)
                        #qq.setMaximumWidth(102)
                        self.HB_layout.addWidget(qq)
                    break
                else:
                    qq = QtWidgets.QWidget()
                    qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                    qq.setLayout(vbox)
                    #qq.setMaximumWidth(102)
                    self.HB_layout.addWidget(qq)

            return True

    def add_new_grade(self, new_str):
        nonexist = True
        items = []
        if new_str != ".":
            for litem in self.grade_list:
                txt = litem.text()
                items.append({"grade": txt})
                if new_str == txt:
                    nonexist = False
            if nonexist is True:
                items.insert(0, {"grade": new_str})
                self.clearLayout(self.HB_layout)
                self.addItemsToQHBox(items)
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", "The grade already exists.")
                )
        else:  # delete empty string from grade list
            for litem in self.grade_list:
                txt = litem.text()
                if txt != '.':
                    items.append({"grade": txt})
            self.clearLayout(self.HB_layout)
            self.addItemsToQHBox(items)


    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item, QtWidgets.QWidgetItem):
                #print("widget" + str(item))
                item.widget().close()
                # or
                # item.widget().setParent(None)
            elif isinstance(item, QtWidgets.QSpacerItem):
                #print("spacer " + str(item))
                # no need to do extra stuff
                pass
            else:
                #print("layout " + str(item))
                self.clearLayout(item.layout())
            # remove the item from layout
            layout.removeItem(item)

