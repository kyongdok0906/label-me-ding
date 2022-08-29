import threading
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtGui import QColor, QColorConstants
from qtpy.QtCore import Qt

from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle
from PyQt5.QtCore import pyqtSlot, QTimer
from .. import utils
from labelme.widgets.custom_qlabel import CQLabel
from labelme.widgets.signal import Signal
from labelme.shape import Shape


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
        self._items.clear()
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
                self._app.sendGradeToServer(new_str, items, self.addItemsToQHBox)
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
    _shape = None
    _checked = True

    def __init__(self, shape=None, parent=None):
        self._shape = shape
        self._parent = parent

        super(RowWidgetItem, self).__init__()
        horizontal_layout = QtWidgets.QHBoxLayout(self)
        horizontal_layout.setSpacing(1)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(self)

        label.setText("#{}  {}".format(self._shape.id, self._shape.label))
        label.setStyleSheet("QWidget { font-size: 12px; }")
        #label.setMaximumWidth(230)

        color_label = QtWidgets.QLabel(self)
        color_txt = self._shape.color

        if not color_txt or "" == color_txt:
            color_txt = "cyan"

        color_label.setText("")
        color_label.setStyleSheet("QLabel{border: 1px soild #aaa; border-radius: 7px; background: %s;}" % color_txt)
        color_label.setFixedWidth(8)

        self.check_box = QtWidgets.QCheckBox(self)

        self.check_box.stateChanged.connect(self.stateChangeHandle)
        self.check_box.setCheckState(Qt.Checked)  # Qt.Checked

        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(label, 0, QtCore.Qt.AlignLeft)
        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(color_label, 0, QtCore.Qt.AlignLeft)
        horizontal_layout.addStretch()
        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(self.check_box, 0, QtCore.Qt.AlignRight)
        horizontal_layout.addSpacing(40)
        self.setLayout(horizontal_layout)
        self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")

        self.setAutoFillBackground(True)

    def mousePressEvent(self, event):
        # print("row click")
        if self._parent is not None:
            #self._shape.selected = True
            self._parent.itemSelectionChangedEvent(self)
            pass

    def changeBackground(self, state):
        if state is True:
            #self._shape.selected = True
            self.setStyleSheet("QWidget { background-color: rgb(204, 232, 255); border: 0; font-size: 12px}")
        else:
            #self._shape.selected = False
            self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")
        self.setAutoFillBackground(True)

    def checkitem(self, flag):
        if flag is True:
            self.check_box.setCheckState(Qt.Checked)
            self._checked = True
        else:
            self.check_box.setCheckState(Qt.Unchecked)
            self._checked = False

    def stateChangeHandle(self, state):
        if state == Qt.Checked:
            # self.signal.polygon_check_signal.emit(1)
            self._checked = True
        else:
            # self.signal.polygon_check_signal.emit(0)
            self._checked = False
        self._parent.labelItemChanged(self)


class CustomLabelListWidget(QtWidgets.QWidget):

    # itemDoubleClicked = QtCore.Signal(CustomLabelListWidgetItem)
    itemSelectionChanged = QtCore.Signal(list, list)

    def __init__(self, app):
        super(CustomLabelListWidget, self).__init__()

        self.signal = Signal()
        self.signal.polygon_check_signal.connect(self.polygon_label_status)
        self._app = app
        self._selected_item = []
        self._itemList = []
        self._items = [
            """
            {
                "label": "철못(기 사용한 것)",
                "COLOR": "red"
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

    def itemSelectionChangedEvent(self, item):
        selected = []
        deselected = []
        for it in range(len(self._itemList)):
            rowItem = self._itemList[it]
            if rowItem._shape.label == item._shape.label and rowItem._shape.id == item._shape.id:
                rowItem.changeBackground(True)
                if self.findSelectedItem(rowItem) is False:
                    self._selected_item.append(rowItem)
                selected.append(rowItem)
            else:
                rowItem.changeBackground(False)
                try:
                    if self.findSelectedItem(rowItem) is True:
                        self._selected_item.remove(rowItem)
                except:
                    pass
                deselected.append(rowItem)
        self.itemSelectionChanged.emit(selected, deselected)

    def labelItemChanged(self, item):
        self._app.labelItemChanged(item)


    def getShapeSelectedItems(self):
        sss = []
        for iem in self._selected_item:
            sss.append(iem._shape)
        return sss

    def addItems(self, shapes):
        if len(items) < 1:
            return
        self._itemList.clear()
        self.clear()
        for shape in shapes:
            rowItem = RowWidgetItem(shape, self)
            self.vContent_layout.addWidget(rowItem)
            self._itemList.append(rowItem)

        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(self.tr("Polygon Labels (Total %s)" % len(self._itemList)))


    def addItem(self, shape):
        if shape:
            rowItem = RowWidgetItem(shape, self)
            self.vContent_layout.addWidget(rowItem)
            self._itemList.append(rowItem)


    def removeItem(self, item):
        if len(self._itemList) < 1:
            return
        try:
            self._itemList.remove(item)
        except:
            pass
        self.clear()
        for it in range(len(self._itemList)):
            rowItem = RowWidgetItem(self._itemList[it]._shape, self)
            self.vContent_layout.addWidget(rowItem)

        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(self.tr("Polygon Labels (Total %s)" % len(self._itemList)))



    def getItems(self):
        if len(self._itemList) > 0:
            return self._itemList
        else:
            return []

    def getCountItems(self):
        return len(self._itemList)

    def getCheckedItems(self):
        checkitems = []
        for it in range(len(self._itemList)):
            item = self._itemList[it]
            if item._checked is True:
                checkitems.append(item)
        return checkitems


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
                item.checkitem(True)
                # item.hide()
        else:
            #show uncheck items
            #print("err", flag)
            for it in range(len(self._itemList)):
                item = self._itemList[it]
                item._selected = False
                item.changeBackground(False)
                item.checkitem(False)
                #item.show()

    def clear(self):
        self.clearLayout(self.vContent_layout)

    def findItemByShape(self, shape):
        for row in range(len(self._itemList)):
            item = self._itemList[row]
            if isinstance(shape, Shape):
                if item._shape == shape:
                    return item
            else:
                if item._shape == shape._shape:
                    return item

        raise ValueError("cannot find shape: {}".format(shape))

    def selectItem(self, pitem):
        for it in range(len(self._itemList)):
            item = self._itemList[it]
            if item == pitem:
                item.changeBackground(True)
                if self.findSelectedItem(item) is False:
                    self._selected_item.append(item)
            else:
                item.changeBackground(False)
                try:
                    if self.findSelectedItem(item) is True:
                        self._selected_item.remove(item)
                except:
                    pass

    def findSelectedItem(self, pitem):
        for item in self._selected_item:
            if item == pitem:
                return True
        return False

    def selectedItems(self):
        return self._selected_item

    def clearSelection(self):
        for item in self._itemList:
            item.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0; font-size: 12px}")

    # signal no using now
    @pyqtSlot(int)
    def polygon_label_status(self, arg):
        #print(arg)
        pass


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
        hbox_layout.setContentsMargins(5, 5, 0, 0)

        #self.polygon = Qlabel(self.tr("polygon"))
        #hbox_layout.addWidget(self.polygon, 0, QtCore.Qt.AlignLeft)

        self.polygon = QToolButton()
        self.polygon.setIcon(utils.newIcon("poly"))
        self.polygon.setIconSize(QtCore.QSize(20, 20))
        self.polygon.clicked.connect(self.polygonClick)
        #self.polygon.setFixedSize(150, 150)

        self.rect = QToolButton()
        self.rect.setIcon(utils.newIcon("rect"))
        self.rect.setIconSize(QtCore.QSize(20, 20))
        self.rect.clicked.connect(self.rectClick)

        self.circle = QToolButton()
        self.circle.setIcon(utils.newIcon("circle"))
        self.circle.setIconSize(QtCore.QSize(20, 20))
        self.circle.clicked.connect(self.circleClick)

        self.line = QToolButton()
        self.line.setIcon(utils.newIcon("line"))
        self.line.setIconSize(QtCore.QSize(20, 20))
        self.line.clicked.connect(self.lineClick)

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

    def polygonClick(self, arg):
        self.polygon.setEnabled(False)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        if self._app is not None:
            self._app.selected_shapType = "polygon"
            self._app.toggleDrawMode(False, createMode="polygon")

    def rectClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(False)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        if self._app is not None:
            self._app.selected_shapType = "rectangle"
            self._app.toggleDrawMode(False, createMode="rectangle")

    def circleClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(False)
        self.line.setEnabled(True)
        if self._app is not None:
            self._app.selected_shapType = "circle"
            self._app.toggleDrawMode(False, createMode="circle")

    def lineClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(False)
        if self._app is not None:
            self._app.selected_shapType = "line"
            self._app.toggleDrawMode(False, createMode="line")

    def editmodeClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)

    def eventFromMenu(self, mode):
        if mode == "polygon":
            self.polygon.setEnabled(False)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
        elif mode == "rectangle":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(False)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
        elif mode == "circle":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(False)
            self.line.setEnabled(True)
        elif mode == "line":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(False)
        else:
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)

