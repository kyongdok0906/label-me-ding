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

# grade list
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
                        lbObj.setStyleSheet("QLabel { border: 0px solid #aaa; padding:2px}")

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
                vbox.setContentsMargins(0, 0, 1, 0)
                vbox.setSpacing(1)
                #vbox.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)
                for i in range(4):
                    if icount < item_count:
                        item = items[icount]
                        if item is not None:
                            qlb = CQLabel(item["grade"], self)
                            # qlb.sizeHint()
                            # qlb.setObjectName(item["grade"])
                            qlb.setStyleSheet("QLabel { border: 0px solid #aaa; padding:2px}")
                            qlb.setMaximumWidth(100)
                            qlb.setMaximumHeight(28)
                            qlb.setFont(self._app._font)
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
                if self._app._config["local_lang"] == "ko_KR":
                    self._app.grade_title_bar.titleLabel.setText("등급 (총 %s)" % len(self.items_list))
                else:
                    self._app.grade_title_bar.titleLabel.setText("Grades (Total %s)" % len(self.items_list))
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

# polygon item
class RowWidgetItem(QtWidgets.QWidget):
    _shape = None
    _checked = True

    def __init__(self, shape=None, parent=None, itemNo=None):
        super(RowWidgetItem, self).__init__()

        if isinstance(shape, Shape):
            self._shape = shape
        else:
            #sp = {"id": shape["id"], "label": shape["label"], "color": shape["color"]}
            sp = Shape()
            sp.label_display = shape["label_display"]
            sp.label = shape["label"]
            sp.grade = shape["grade"]
            sp.color = shape["color"]
            self._shape = sp
        #self._shape = shape
        self._parent = parent

        horizontal_layout = QtWidgets.QHBoxLayout(self)
        horizontal_layout.setSpacing(0)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(self)
        if itemNo is not None:
            if itemNo < 10000:
                idx = "%04d" % itemNo
            else:
                idx = "%08d" % itemNo
        else:
            idx = len(self._parent._itemList)
            if idx < 10000:
                idx = "%04d" % idx
            else:
                idx = "%08d" % idx

        self._id = idx
        self.label.setText("#{}  {}".format(self._id, self._shape.label_display))
        #label.setStyleSheet("QWidget { font-size: 18px; }")
        self._font = QtGui.QFont("맑은 고딕", 10, QtGui.QFont.Normal)
        if self._font:
            self.label.setFont(self._font)

        self.color_label = QtWidgets.QLabel(self)
        color_txt = self._shape.color

        if not color_txt or "" == color_txt:
            color_txt = "cyan"

        self.color_label.setText("")
        self.color_label.setStyleSheet("QLabel{border: 1px soild #aaa; border-radius: 7px; background: %s;}" % color_txt)
        self.color_label.setFixedWidth(8)

        self.check_box = QtWidgets.QCheckBox(self)

        self.check_box.stateChanged.connect(self.stateChangeHandle)
        self.check_box.setCheckState(Qt.Checked)  # Qt.Checked

        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(self.label, 0, QtCore.Qt.AlignLeft)
        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(self.color_label, 0, QtCore.Qt.AlignLeft)
        horizontal_layout.addStretch()
        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(self.check_box, 0, QtCore.Qt.AlignRight)
        horizontal_layout.addSpacing(40)
        self.setLayout(horizontal_layout)
        self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0;}")

        self.setAutoFillBackground(True)


    def enterEvent(self, event):
        print("enterEvent", self._id)


    def reSetName(self, num):
        if num < 10000:
            idx = "%04d" % num
        else:
            idx = "%08d" % num
        self._id = idx
        self.label.setText("#{}  {}".format(self._id, self._shape.label_display))

    def mousePressEvent(self, event):
        if self._parent is not None:
            self._parent.itemSelectionChangedEvent(self)

    def changeBackground(self, state):
        if state is True:
            #self._shape.selected = True
            self.setStyleSheet("QWidget { background-color: rgb(204, 232, 255); border: 0;}")
        else:
            #self._shape.selected = False
            self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0;}")
        self.setAutoFillBackground(True)

    def changeTextAndBackground(self):
        self.label.setText("#{}  {}".format(self._id, self._shape.label_display))
        self.label.repaint()
        color_txt = self._shape.color
        if not color_txt or "" == color_txt:
            color_txt = "cyan"
        self.color_label.setStyleSheet(
            "QLabel{border: 1px soild #aaa; border-radius: 7px; background: %s;}" % color_txt)
        self.changeBackground(True)
        self.repaint()
        #self.color_label.repaint()

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

# polygon list
class CustomLabelListWidget(QtWidgets.QWidget):
    # itemDoubleClicked = QtCore.Signal(CustomLabelListWidgetItem)
    #itemSelectionChanged = QtCore.Signal(list, list)
    itemSelectionChanged = QtCore.Signal(list)

    def __init__(self, app):
        super(CustomLabelListWidget, self).__init__()
        #self.signal = Signal()
        #self.signal.polygon_check_signal.connect(self.polygon_label_status)
        self._app = app
        self._selected_item = []
        self._itemList = []
        self.setAcceptDrops(True)

        self.initUI()
        #if self._app._font:
        #    self.setFont(self._app._font)

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

    def itemSelectionChangedEvent(self, item):
        selected = []
        selected.append(item)
        self.itemSelectionChanged.emit(selected)

    # status of checkbox
    def labelItemChanged(self, item):
        self._app.labelItemChanged(item)

    def getShapeSelectedItems(self):
        sss = []
        for iem in self._selected_item:
            sss.append(iem._shape)
        return sss

    def addItems(self, shapes):
        if len(shapes) < 1:
            return
        self.clear()
        for shape in shapes:
            rowItem = RowWidgetItem(shape, self)
            self.vContent_layout.addWidget(rowItem)
            self._itemList.append(rowItem)

        polyT = "Polygon Labels (Total %s)"
        if self._app._config["local_lang"] == "ko_KR":
            polyT = "다각형 레이블 (총 %s)"
        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self._itemList))


    def addItem(self, shape):
        if shape:
            T = self.findItemByShape(shape)
            if T is None:
                rowItem = RowWidgetItem(shape, self)
                self.vContent_layout.addWidget(rowItem)
                self._itemList.append(rowItem)


    def removeItem(self, item):
        if len(self._itemList) < 1:
            return
        try:
            for i in reversed(range(self.vContent_layout.count())):
                vitem = self.vContent_layout.itemAt(i)
                if isinstance(vitem, QtWidgets.QWidgetItem):
                    # print("widget" + str(item))
                    vw = vitem.widget()
                    if vw == item:
                        vw.close()
                        self.vContent_layout.removeItem(vitem)
                        self._itemList.remove(item)
                        break
        except:
            utils.qt.LogPrint('except in removeItem custom_list_widget.py')

    def list_label_resort(self):
        for i in reversed(range(self.vContent_layout.count())):
            vitem = self.vContent_layout.itemAt(i)
            if isinstance(vitem, QtWidgets.QWidgetItem):
                vw = vitem.widget()
                if isinstance(vw, RowWidgetItem):
                    vw.reSetName(i)

        polyT = "Polygon Labels (Total %s)"
        if self._app._config["local_lang"] == "ko_KR":
            polyT = "다격형 레이블 (총 %s)"
        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self._itemList))
        self.repaint()

    # no using now
    def list_label_repaint(self):
        self.clearlistLayout()
        for row in range(len(self._itemList)):
            rowItem = RowWidgetItem(self._itemList[row]._shape, self, row)
            self.vContent_layout.addWidget(rowItem)
        #self._selected_item.clear()
        polyT = "Polygon Labels (Total %s)"
        if self._app._config["local_lang"] == "ko_KR":
            polyT = "다격형 레이블 (총 %s)"
        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self._itemList))
        self.repaint()

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
                item.changeBackground(False)
                item.checkitem(False)
                #item.show()

    def clear(self):
        self._itemList.clear()
        self._selected_item.clear()

    def clearlistLayout(self):
        self.clearLayout(self.vContent_layout)

    def findItemByShape(self, shape):
        if len(self._itemList) < 1:
            return None
        for row in range(len(self._itemList)):
            item = self._itemList[row]
            if isinstance(shape, Shape):
                if item._shape == shape:
                    return item
            else:
                if item._shape == shape._shape:
                    return item
        # utils.qt.LogPrint("cannot find shape: {}".format(shape.label).encode('utf-8'))
        return None
        #raise ValueError("cannot find shape: {}".format(shape))

    def selectItem(self, pitem):
        for it in range(len(self._itemList)):
            item = self._itemList[it]
            if item == pitem:
                item.changeBackground(True)
                item.repaint()
                # T, x = self.findSelectedItem(item)
                # if T is False:
                self._selected_item.append(item)
                break

    def findSelectedItem(self, pitem):
        i = 0
        for item in self._selected_item:
            if item == pitem:
                return True, i
            i = i + 1
        return False, -1

    def findItem(self, pitem):
        for row in range(len(self._itemList)):
            item = self._itemList[row]
            if item == pitem:
                return True
        return False

    def selectedItems(self):
        return self._selected_item

    def clearSelection(self):
        for item in self._itemList:
            item.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0;}")
        self._selected_item.clear()

    # signal no using now
    @pyqtSlot(int)
    def polygon_label_status(self, arg):
        #print(arg)
        pass

    def mousePressEvent(self, event):
        self.itemSelectionChanged.emit([])

    def dragMoveEvent(self, event):
        print("dragMoveEvent")

    def dragEnterEvent(self, event):
        print("dragEnterEvent")

    def keyPressEvent(self, ev):
        return
        modifiers = ev.modifiers()
        key = ev.key()
        if key == QtCore.Qt.Key_Control:
            print("ctrl + ")
        if QtCore.Qt.ControlModifier == int(modifiers):
            print("ctrl + 111")

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

        if self._app._font:
            self.setFont(self._app._font)

    def initUI(self):
        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(0)
        hbox_layout.setContentsMargins(5, 5, 0, 0)

        self.polygon = QToolButton()
        self.polygon.setIcon(utils.newIcon("poly"))
        self.polygon.setIconSize(QtCore.QSize(20, 20))
        self.polygon.clicked.connect(self.polygonClick)
        self.polygon.setEnabled(False)
        #self.polygon.setFixedSize(150, 150)

        self.rect = QToolButton()
        self.rect.setIcon(utils.newIcon("rect"))
        self.rect.setIconSize(QtCore.QSize(20, 20))
        self.rect.clicked.connect(self.rectClick)
        self.rect.setEnabled(False)

        self.circle = QToolButton()
        self.circle.setIcon(utils.newIcon("circle"))
        self.circle.setIconSize(QtCore.QSize(20, 20))
        self.circle.clicked.connect(self.circleClick)
        self.circle.setEnabled(False)

        self.line = QToolButton()
        self.line.setIcon(utils.newIcon("line"))
        self.line.setIconSize(QtCore.QSize(20, 20))
        self.line.clicked.connect(self.lineClick)
        self.line.setEnabled(False)

        self.arrow = QToolButton()
        self.arrow.setIcon(utils.newIcon("CursorArrow"))
        self.arrow.setIconSize(QtCore.QSize(20, 20))
        self.arrow.clicked.connect(self.arrowClick)
        self.arrow.setEnabled(False)

        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.polygon, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.rect, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.circle, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.line, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.arrow, 0, QtCore.Qt.AlignLeft)

        hbox_layout.addStretch()

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

    def arrowClick(self):
        self._app.toggleDrawMode(True)
        #self._app.canvas.setEnabled(False)
        self._app.canvas.overrideCursor(QtCore.Qt.ArrowCursor)

    def editmodeClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        self.arrow.setEnabled(True)

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
            self.arrow.setEnabled(True)

