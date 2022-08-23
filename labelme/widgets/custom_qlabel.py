# imports
from qtpy import QtGui
from qtpy.QtWidgets import QLabel


class CQLabel(QLabel):
    def __init__(self, txt, parent):
        super(CQLabel, self).__init__()
        self.setText(txt)
        self.setContentsMargins(3, 3, 3, 3)
        self._parent = parent
        # self.show()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        # print("click " + self.text())
        self.setStyleSheet("QWidget { background-color: rgba(10, 170, 255, 80); border: 0; font-size: 12px}")
        self._parent.selected_grade = self.text()
        self._parent.event_mouse_click()
