from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from hexview import HexDisplay
from collections import OrderedDict

def padhex(val, length):
    return "0x{}".format('0'*(length - len(hex(val)))) + hex(val).split('0x')[1]

class TracebackWindow(QtWidgets.QWidget):

    def __init__(self):
        super(TracebackWindow, self).__init__()

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._textBrowser = QtWidgets.QTextBrowser()
        self._layout.addWidget(self._textBrowser)

        self._ret = QtWidgets.QLabel()
        self._layout.addWidget(self._ret)

        self.setObjectName('Traceback_Window')

    def update_frames(self, framelist):
        self._textBrowser.clear()
        padlength = max([len(hex(frame['addr'])) for frame in framelist])
        for row, frame in enumerate(framelist[::-1]):
            self._textBrowser.insertPlainText("{}. ".format(len(framelist) - frame['index']))
            self._textBrowser.insertPlainText("  "*row + padhex(frame['addr'], padlength) + ' in ' + frame['name'])
            self._textBrowser.insertPlainText("\n")

    def update_ret_address(self, addr, label=None):
        if label is not None:
            self._ret.setText("Return address: {} in ".format(hex(addr)) + label)
        else:
            self._ret.setText("Return address: {}".format(hex(addr)))
