from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import QEvent, Qt
from qtpy.QtWidgets import QGridLayout, QHBoxLayout, \
    QLabel, QLineEdit, QToolButton, QDockWidget, QStyle, QApplication, QCheckBox
from keyboard import press
from labelme.widgets.signal import Signal
from .. import utils


class DockInPutTitleBar(QtWidgets.QWidget):
    def __init__(self, dockWidget, bartype, app):
        super(DockInPutTitleBar, self).__init__(dockWidget)
        self._bartype = bartype
        self._app = app
        self._dockWidget = dockWidget

        boxLayout = QHBoxLayout(self)
        boxLayout.setSpacing(1)
        boxLayout.setContentsMargins(1, 1, 1, 1)

        self.titleLabel = QLabel(self)
        if self._bartype == "gradesbar":
            self.titleLabel.setText(self.tr("Grades (Total %s)" % 0))
        if self._bartype == "productsbar":
            self.titleLabel.setText(self.tr("Products (Total %s)" % 0))

        self.hidnBtn = QtWidgets.QPushButton(self)
        self.hidnBtn.setText('.')
        self.hidnBtn.setFixedWidth(10)
        self.hidnBtn.clicked.connect(self.clickProgramicallyBtn)  # must click this button Programically
        self.hidnBtn.hide()

        if self._bartype == "gradesbar" and self._app._config["grade_yn"] == "Y":
            self.newLabel = QLabel(str("New Input"))
            self.titleEdit = QLineEdit(self)
            # self.titleEdit.hide()
            #self.titleEdit.editingFinished.connect(self.finishEdit)
            self.titleEdit.returnPressed.connect(self.returnPresshandle)

        elif self._bartype == "productsbar" and self._app._config["product_yn"] == "Y":
            self.newLabel = QLabel(str("New Input"))
            self.titleEdit = QLineEdit(self)
            # self.titleEdit.hide()
            #self.titleEdit.editingFinished.connect(self.finishEdit)
            self.titleEdit.returnPressed.connect(self.returnPresshandle)

        """
         iconSize = QApplication.style().standardIcon(
            QStyle.SP_TitleBarNormalButton).actualSize(
                QtCore.QSize(100, 100))
        buttonSize = iconSize + QtCore.QSize(4, 4)
        """

        self.dockButton = QToolButton(self)
        #self.dockButton.setIcon(QApplication.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.dockButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarNormalButton")))
        self.dockButton.setFixedSize(14, 14)
        #self.dockButton.setMaximumSize(buttonSize)
        self.dockButton.setAutoRaise(True)
        self.dockButton.clicked.connect(self.toggleFloating)

        self.closeButton = QToolButton(self)
        self.closeButton.setFixedSize(14, 14)
        #self.closeButton.setMaximumSize(buttonSize)
        self.closeButton.setAutoRaise(True)
        #self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
        self.closeButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton")))
        self.closeButton.clicked.connect(self.closeParent)

        boxLayout.addSpacing(6)
        boxLayout.addWidget(self.titleLabel, 0, QtCore.Qt.AlignLeft)
        boxLayout.addWidget(self.hidnBtn, 0, QtCore.Qt.AlignLeft)
        boxLayout.addStretch()
        boxLayout.addSpacing(20)

        if self._bartype == "gradesbar" and self._app._config["grade_yn"] == "Y":
            boxLayout.addWidget(self.newLabel, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(6)
            boxLayout.addWidget(self.titleEdit, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(5)

        elif self._bartype == "productsbar" and self._app._config["product_yn"] == "Y":
            boxLayout.addWidget(self.newLabel, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(6)
            boxLayout.addWidget(self.titleEdit, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(5)

        boxLayout.addWidget(self.dockButton, 0, QtCore.Qt.AlignRight)
        boxLayout.addSpacing(5)
        boxLayout.addWidget(self.closeButton, 0, QtCore.Qt.AlignRight)

        dockWidget.featuresChanged.connect(self.onFeaturesChanged)

        self.onFeaturesChanged(dockWidget.features())
        # self.setTitle(dockWidget.windowTitle())

        dockWidget.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.WindowTitleChange:
            pass
            #self.setTitle(source.windowTitle())
        return super(DockInPutTitleBar, self).eventFilter(source, event)

    def startEdit(self):
        #print("startEdit")
        #self.titleLabel.hide()
        #self.titleEdit.show()
        #self.titleEdit.setFocus()
        pass

    def finishEdit(self):
        #self.titleEdit.hide()
        #self.titleLabel.show()
        #self.parent().setWindowTitle(self.titleEdit.text())
        #print("finishEdit")
        pass

    def returnPresshandle(self):  # called when it press enter key
        input_str = self.titleEdit.text()
        re_str = input_str.strip()
        if len(re_str) < 1:
            return

        if self._bartype == "gradesbar":
            _customlistwidget = self._dockWidget.widget()
            if _customlistwidget and len(_customlistwidget.items_list) > 0:
                _customlistwidget.addNewGrade(re_str)
                self.titleEdit.setText("")

        if self._bartype == "productsbar":
            # print(self.objectName() + re_str)
            _customlistwidget = self._dockWidget.widget()
            if _customlistwidget and self._app:
                self._app.sendProductToServer(re_str, self._app.addProduct)
                self.titleEdit.setText("")

    def onFeaturesChanged(self, features):
        if not features & QDockWidget.DockWidgetVerticalTitleBar:
            self.closeButton.setVisible(
                features & QDockWidget.DockWidgetClosable)
            self.dockButton.setVisible(
                features &
                QDockWidget.DockWidgetFloatable)
        else:
            raise ValueError('vertical title bar not supported')

    def setTitle(self, title):
        self.titleLabel.setText(title)
        #self.titleEdit.setText(title)

    def toggleFloating(self):
        self.parent().setFloating(not self.parent().isFloating())

    def closeParent(self):
        self.parent().toggleViewAction().setChecked(False)
        self.parent().hide()

    def mouseDoubleClickEvent(self, event):
        if event.pos().x() <= self.titleLabel.width():
            self.startEdit()
        else:
            # this keeps the normal double-click behaviour
            super(DockInPutTitleBar, self).mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    # polygon list add event
    def clickProgramicallyBtn(self):
        self._app.receiveGradesFromServer()

    # non using
    def pressEnterKeyForce(self):
        self.titleEdit.setFocus()
        self.titleEdit.setText("")
        press('enter')


class DockCheckBoxTitleBar(QtWidgets.QWidget):
    def __init__(self, app, dockWidget):
        super(DockCheckBoxTitleBar, self).__init__(dockWidget)
        self._app = app
        #self.signal = Signal()
        #self.signal.polygon_check_signal.connect(self.polygon_label_status)
        boxLayout = QHBoxLayout(self)
        boxLayout.setSpacing(1)
        boxLayout.setContentsMargins(1, 1, 1, 1)

        self.titleLabel = QLabel(self)
        self.titleLabel.setText(self.tr("Polygon Labels (Total %s)" % 0))

        self.hidnBtn = QtWidgets.QPushButton(self)
        self.hidnBtn.setText('')
        self.hidnBtn.setFixedWidth(10)
        self.hidnBtn.clicked.connect(self.clickProgramicallyBtn)  # must click this button Programically
        self.hidnBtn.hide()

        self.checkbox = QCheckBox(self)
        self.checkbox.stateChanged.connect(self.stateChangeHandle)
        self.checkbox.setCheckState(Qt.Checked)

        self.dockButton = QToolButton(self)
        #self.dockButton.setIcon(QApplication.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.dockButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarNormalButton")))
        self.dockButton.setFixedSize(14, 14)
        #self.dockButton.setMaximumSize(buttonSize)
        self.dockButton.setAutoRaise(True)
        self.dockButton.clicked.connect(self.toggleFloating)

        self.closeButton = QToolButton(self)
        self.closeButton.setFixedSize(14, 14)
        #self.closeButton.setMaximumSize(buttonSize)
        self.closeButton.setAutoRaise(True)
        #self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
        self.closeButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton")))
        self.closeButton.clicked.connect(self.closeParent)

        boxLayout.addSpacing(6)
        boxLayout.addWidget(self.titleLabel, 0, QtCore.Qt.AlignLeft)
        boxLayout.addWidget(self.hidnBtn, 0, QtCore.Qt.AlignLeft)
        boxLayout.addStretch()
        boxLayout.addWidget(self.checkbox, 0, QtCore.Qt.AlignRight)
        boxLayout.addSpacing(5)
        boxLayout.addWidget(self.dockButton, 0, QtCore.Qt.AlignRight)
        boxLayout.addSpacing(5)
        boxLayout.addWidget(self.closeButton, 0, QtCore.Qt.AlignRight)

        dockWidget.featuresChanged.connect(self.onFeaturesChanged)

        self.onFeaturesChanged(dockWidget.features())
        #self.setTitle(dockWidget.windowTitle())

        dockWidget.installEventFilter(self)
        self.setContentsMargins(0, 3, 0, 5)
        # self.setStyleSheet("QWidget { background: rgb(222, 222, 222); }")

    def eventFilter(self, source, event):
        #if event.type() == QEvent.WindowTitleChange:
        #    self.setTitle(source.windowTitle())
        return super(DockCheckBoxTitleBar, self).eventFilter(source, event)


    def onFeaturesChanged(self, features):
        if not features & QDockWidget.DockWidgetVerticalTitleBar:
            self.closeButton.setVisible(
                features & QDockWidget.DockWidgetClosable)
            self.dockButton.setVisible(
                features &
                QDockWidget.DockWidgetFloatable)
        else:
            raise ValueError('vertical title bar not supported')

    def setTitle(self, title):
        self.titleLabel.setText(title)

    def stateChangeHandle(self, state):
        if state == Qt.Checked:
            #self.signal.polygon_check_signal.emit(1)
            #self._app.labelList.showItems(True)
            self._app.togglePolygons(True)
        else:
            #self.signal.polygon_check_signal.emit(0)
            #self._app.labelList.showItems(False)
            self._app.togglePolygons(False)

    # receiver function signal
    def polygon_label_status(self, arg):
        print(arg)

    def toggleFloating(self):
        self.parent().setFloating(not self.parent().isFloating())

    def closeParent(self):
        self.parent().toggleViewAction().setChecked(False)
        self.parent().hide()

    # polygon list add event
    def clickProgramicallyBtn(self):
        self._app.receiveLabelsFromServerByGrade()


# The class don't using now
class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, objname, parentDock, app=None):
        super(CustomTitleBar, self).__init__()
        self.setObjectName(objname)
        self.setMaximumHeight(22)
        self.setContentsMargins(5, 0, 5, 2)
        # self.setStyleSheet("QWidget { border: 1px solid #aaa;} ")
        self._parent_dock = parentDock
        self._app = app
        # setting UI

        self.initUI()

    def initUI(self):
        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(6)
        hbox_layout.setContentsMargins(0, 0, 0, 0)

        if self.objectName() == "gradesbar":
            self.title_lb = QLabel(self.tr("Grades (Total %s)" % 0))
        elif self.objectName() == "productsbar":
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

    def setTitleCount(self, count: str):
        self.title_lb.setText(count)

    def closeActionEventHandle(self):
        self._parent_dock.close()

    def toggleActionEventHandle(self):
        self._parent_dock.setFloating(True)

    '''
    def pressEnterKeyForce(self):
        press('enter') # event of enter key
    '''


    def press_input_handle(self):
        input_str = self.input_line_edit.text()
        re_str = input_str.strip()
        if self.objectName() == "gradesbar":
            _customlistwidget = self._parent_dock.widget()
            if _customlistwidget and len(_customlistwidget.items_list) > 0:
                _customlistwidget.addNewGrade(re_str)
                self.input_line_edit.setText("")

        if self.objectName() == "productsbar":
            if len(re_str) < 1:
                return
            #print(self.objectName() + re_str)
            _customlistwidget = self._parent_dock.widget()
            if _customlistwidget and self._app:
                self._app.sendProductToServer(re_str, self._app.addProduct)
                self.input_line_edit.setText("")
