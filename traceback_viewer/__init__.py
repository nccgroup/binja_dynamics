from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFontDatabase

def padhex(val, length):
    return "0x{}".format('0'*(length - len(hex(val)))) + hex(val).split('0x')[1]

class TracebackWindow(QtWidgets.QWidget):
    """ Displays the traceback of the current execution, as retrieved from GDB/LLDB """
    def __init__(self):
        super(TracebackWindow, self).__init__()
        self.framelist = []
        self.ret_add = 0x0
        self.setWindowTitle("Traceback")
        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        # Creates the rich text viewer that displays the traceback
        self._textBrowser = QtWidgets.QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._textBrowser.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self._layout.addWidget(self._textBrowser)

        # Creates the button that displays the return address
        self._ret = QtWidgets.QPushButton()
        self._ret.setFlat(True)
        self._layout.addWidget(self._ret)

        self.resize(self.width(), int(self.height() * 0.5))

        self.setObjectName('Traceback_Window')

    def update_frames(self, framelist):
        """ Renders the list of frames delivered to the traceback viewer and sets
        hyperlinks on the addresses of each function within the binary """
        self._textBrowser.clear()
        padlength = max([len(hex(frame['addr'])) for frame in framelist])
        for row, frame in enumerate(framelist[::-1]):
            self._textBrowser.insertPlainText("{}. ".format(len(framelist) - frame['index']))
            try:
                self._textBrowser.insertHtml(" &nbsp;"*row + '<a href=\"{}\">'.format(frame['addr']) +  padhex(frame['addr'], padlength) + '</a>' + ' in ' + frame['name'])
            except TypeError:
                print("Something went wrong with the traceback")
            self._textBrowser.insertPlainText("\n")
        self.framelist = framelist

    def update_ret_address(self, addr, label=None):
        """ Displays the return address. No highlight-on-change currently """
        if label is not None:
            self._ret.setText("Return address: {} in ".format(hex(addr)) + label)
        else:
            self._ret.setText("Return address: {}".format(hex(addr)))
        self.ret_add = addr

    def set_button_handler(self, callback):
        """ Sets a callback that will be executed with the return address
        as an argument whenver the button is clicked. Used by this project to
        navigate to the address if it's within scope. """
        self._ret.clicked.connect(lambda: callback(self.ret_add))

    def set_hyperlink_handler(self, callback):
        """ Sets a callback that will be called with the anchor text whenever a hyperlink
        in the text browser is clicked. Also used for navigation. """
        self._textBrowser.anchorClicked.connect(callback)
