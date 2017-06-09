from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from hexview import HexDisplay
from collections import OrderedDict
from functools import partial

def padhex(val, length):
    return "0x{}".format('0'*(length - len(hex(val)))) + hex(val).split('0x')[1]

class TracebackWindow(QtWidgets.QWidget):

    def __init__(self):
        super(TracebackWindow, self).__init__()
        self.framelist = []
        self.ret_add = 0x0

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._textBrowser = QtWidgets.QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._layout.addWidget(self._textBrowser)

        self._ret = QtWidgets.QPushButton()
        self._ret.setFlat(True)
        self._layout.addWidget(self._ret)

        self.setObjectName('Traceback_Window')

    def update_frames(self, framelist):
        self._textBrowser.clear()
        padlength = max([len(hex(frame['addr'])) for frame in framelist])
        for row, frame in enumerate(framelist[::-1]):
            self._textBrowser.insertPlainText("{}. ".format(len(framelist) - frame['index']))
            self._textBrowser.insertHtml(" &nbsp;"*row + '<a href=\"{}\">'.format(frame['addr']) +  padhex(frame['addr'], padlength) + '</a>' + ' in ' + frame['name'])
            self._textBrowser.insertPlainText("\n")
        self.framelist = framelist

    def update_ret_address(self, addr, label=None):
        if label is not None:
            self._ret.setText("Return address: {} in ".format(hex(addr)) + label)
        else:
            self._ret.setText("Return address: {}".format(hex(addr)))
        self.ret_add = addr

    def set_button_handler(self, callback):
        self._ret.clicked.connect(lambda: callback(self.ret_add))

    def set_hyperlink_handler(self, callback):
        self._textBrowser.anchorClicked.connect(callback)
