# imports
from qtpy import QtGui
from qtpy.QtWidgets import QLabel


class CQLabel(QLabel):
    def __init__(self, txt, parent):
        super(CQLabel, self).__init__()
        self.setText(txt)
        self.setContentsMargins(3, 3, 3, 3)
        self._parent = parent

        self._font = QtGui.QFont("맑은 고딕", 10, QtGui.QFont.Normal)
        if self._font:
            self.setFont(self._font)
        # self.show()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        # print("click " + self.text())
        self.setStyleSheet("QWidget { background-color: rgb(204, 232, 255); border: 0;}")
        self._parent._selected_item = self.text()
        self._parent.itemClickEventHandle()
