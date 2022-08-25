import threading
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt

from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle
from PyQt5.QtCore import pyqtSlot, QTimer
from .. import utils
from labelme.widgets.custom_qlabel import CQLabel
from labelme.widgets.signal import Signal


class CustomListWidget(QtWidgets.QWidget):
    def __init__(self, _app=None, objtag=None):
        self.items_list = []
        self._app = _app
        self._selected_item = None
        self._objtag = objtag
        self._items = []
        self._status = False

        super(CustomListWidget, self).__init__()
        self.initUI()

    def initUI(self):

        self.HB_layout = QHBoxLayout()
        self.HB_layout.setContentsMargins(6, 6, 6, 6)
        self.HB_layout.setSpacing(0)
        self.HB_layout.setSizeConstraint(QLayout.SetMinimumSize)
        #self.HB_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # refer here funtion addItemsToQHBox

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

    def set(self, items):
        self._items = items
        self.addItemsToQHBox(self._items)

    def get(self):
        return self._items

    def itemClickEventHandle(self):
        # process ploygon with one selected product
        if self._selected_item is not None and self._objtag == "grades":
            self._app.selected_grade = self._selected_item
            threading.Timer(0.1, self._app.receiveProductsFromServerByGrade).start()
            threading.Timer(0.1, self._app.customLabelTitleBar.hidnBtn.clicked.emit).start()
            # self._app.queueEvent(self._app.receiveProductsFromServerByGrade)
            # self._app.queueEvent(self._app.customLabelTitleBar.hidnBtn.clicked.emit)

        elif self._selected_item is not None and self._objtag == "products":
            pass  # process ploygon with one selected product

        if len(self.items_list) > 0:
            item_count = len(self.items_list)
            for j in range(0, item_count):
                lbObj = self.items_list.__getitem__(j)
                if lbObj is not None:
                    txt = lbObj.text()
                    objname = lbObj.objectName()  # will do using after this val
                    if txt != self._selected_item:
                        lbObj.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")

    def addItemsToQHBox(self, items):
        if len(items) > 0:
            self._status = False
            self.clearLayout(self.HB_layout)

            self.items_list.clear()
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
                            self.items_list.append(qlb)
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

            if self._app.grade_title_bar:
                self._app.grade_title_bar.titleLabel.setText(self.tr("Grades (Total %s)" % len(self.items_list)))
            self._status = True

    def addNewGrade(self, new_str):
        nonexist = True
        items = []
        if new_str != "":
            for litem in self.items_list:
                txt = litem.text()
                items.append({"grade": txt})
                if new_str == txt:
                    nonexist = False
            if nonexist is True:
                items.insert(0, {"grade": new_str})
                self._app.sendGradeToServer(items, self.addItemsToQHBox)
                #self.addItemsToQHBox(items)
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", "The grade already exists.")
                )
        else:  # delete empty string from grade list
            for litem in self.items_list:
                txt = litem.text()
                if txt:
                    items.append({"grade": txt})
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


class RowWidgetItem(QtWidgets.QWidget):
    _data = {}
    _selected = False

    def __init__(self, item, parent=None):
        self._data = item
        self._parent = parent

        super(RowWidgetItem, self).__init__()
        horizontal_layout = QtWidgets.QHBoxLayout(self)
        horizontal_layout.setSpacing(1)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(self)
        label.setText(item["label"])
        #label.setStyleSheet("QWidget { font-size: 12px; }")
        check_box = QtWidgets.QCheckBox(self)

        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(label, 0, QtCore.Qt.AlignLeft)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(check_box, 0, QtCore.Qt.AlignRight)
        horizontal_layout.addSpacing(40)
        self.setLayout(horizontal_layout)
        self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")

        self.setAutoFillBackground(True)

    def mousePressEvent(self, event):
        print("row click")
        if self._parent is not None:
            self._parent.mousePressEventHandle(event, self._data)

    def changeBackground(self, state):
        if state is True:
            self.setStyleSheet("QWidget { background-color: rgb(204, 232, 255); border: 0; font-size: 12px}")
        else:
            self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")
        self.setAutoFillBackground(True)




class CustomLabelListWidget(QtWidgets.QWidget):

    # itemDoubleClicked = QtCore.Signal(CustomLabelListWidgetItem)
    # itemSelectionChanged = QtCore.Signal(list, list)

    def __init__(self, parent):
        super(CustomLabelListWidget, self).__init__()

        self.signal = Signal()
        self.signal.polygon_check_signal.connect(self.polygon_label_status)

        self._checkedItems = []
        self._app = parent
        self._itemList = []
        self._model = False
        self._items = [
            """
            {
                "label": "철못(기 사용한 것)"
            }
            """
        ]
        self.initUI()

    def initUI(self):
        self.vContent_layout = QtWidgets.QVBoxLayout(self)
        self.vContent_layout.setContentsMargins(0, 5, 0, 5)
        self.vContent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.twidget = QtWidgets.QWidget(self)
        self.twidget.setLayout(self.vContent_layout)
        self.twidget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255);}")
        scroll = QScrollArea()
        scroll.setWidget(self.twidget)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)

        hb_layout = QHBoxLayout()
        hb_layout.addWidget(scroll)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        hb_layout.setSpacing(0)
        self.setLayout(hb_layout)

        '''
        its = [{'label': '폐선박 해체(중량 A 이외의 것)'}, {'label': '철근말이'}, {'label': '절단 스크랩(철재, 철판 구조물, 중량A 이외의 것)'}]
            self.addRows(its)
        '''

    def mousePressEventHandle(self, event, pdata):
        # print("list row click")
        for it in range(len(self._itemList)):
            rowItem = self._itemList[it]
            if rowItem._data == pdata:
                rowItem.changeBackground(True)
                rowItem._selected = True
            else:
                rowItem.changeBackground(False)
                rowItem._selected = False


    def addRows(self, items):
        if len(items) < 1:
            return
        self._itemList.clear()
        self.clearLayout(self.vContent_layout)

        for it in range(len(items)):
            rowItem = RowWidgetItem(items[it], self)
            self.vContent_layout.addWidget(rowItem)
            self._itemList.append(rowItem)

        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(self.tr("Polygon Labels (Total %s)" % len(self._itemList)))
        self._model = True

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

    # event check box
    def showItems(self, flag):
        if flag == 1:
            #hide items check
            #print("ok", flag)
            for it in range(len(self._itemList)):
                item = self._itemList[it]
                item.hide()

        else:
            #show uncheck items
            #print("err", flag)
            for it in range(len(self._itemList)):
                item = self._itemList[it]
                item._selected = False
                item.changeBackground(False)
                item.show()

    # signal no using now
    @pyqtSlot(int)
    def polygon_label_status(self, arg):
        print(arg)


class topToolWidget(QtWidgets.QWidget):
    def __init__(self, objname, app=None):
        super(topToolWidget, self).__init__()
        self.setObjectName(objname)
        self.setMaximumHeight(50)
        self.setContentsMargins(0, 0, 0, 0)
        # self.setFixedWidth(500)
        self._app = app
        # setting UI

        self.initUI()

    def initUI(self):
        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(0)
        hbox_layout.setContentsMargins(0, 0, 0, 0)

        #self.polygon = Qlabel(self.tr("polygon"))
        #hbox_layout.addWidget(self.polygon, 0, QtCore.Qt.AlignLeft)

        self.polygon = QToolButton()
        self.polygon.setIcon(utils.newIcon("poly"))
        #self.polygon.setFixedSize(50, 50)

        self.rect = QToolButton()
        self.rect.setIcon(utils.newIcon("rect"))

        self.circle = QToolButton()
        self.circle.setIcon(utils.newIcon("circle"))

        self.line = QToolButton()
        self.line.setIcon(utils.newIcon("line"))

        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.polygon, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.rect, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.circle, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.line, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addStretch(1)

        self.setLayout(hbox_layout)
