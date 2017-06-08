from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from hexview import HexDisplay
from collections import OrderedDict

class TracebackWindow(QtWidgets.QWidget):

    def __init__(self):
        super(TracebackWindow, self).__init__()

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self.setObjectName('Traceback_Window')
