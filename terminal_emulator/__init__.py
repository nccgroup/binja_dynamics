from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QTextCursor, QIcon
from base64 import b64decode

import pty, select, os
from queue import Queue
from functools import partial

from binaryninja import log_alert

usercolor = QColor(255, 153, 51)

class TerminalThread(QThread):
    RECV_LINE = pyqtSignal(str)

    def __init__(self, message_q):
        QThread.__init__(self)
        self.messages = message_q
        self.master, self.slave = pty.openpty()
        self.tty = os.ttyname(self.slave)
        self.dirty = False

    def __del__(self):
        os.close(self.master)
        os.close(self.slave)

    def run(self):
        while True :
            writefd = []
            if not self.messages.empty():
                message = self.messages.get()
                if message == 'exit':
                    self.messages.task_done()
                    break
                else:
                    message, _encoding = message
                    writefd = [self.master]
            r,w,_ = select.select([self.master], writefd, [], 0)
            if not r:
                self.dirty = False
            if r and not self.dirty:
                line = os.read(self.master, 1024)
                self.RECV_LINE.emit(line)
            if w:
                os.write(self.master, message + "\n")
                self.messages.task_done()
                self.dirty = True

class TerminalWindow(QtWidgets.QWidget):

    def __init__(self):
        super(TerminalWindow, self).__init__()
        self._encodings = ['raw', 'hex', 'b64', 'py2']
        self.framelist = []
        self.setWindowTitle("Binary Interaction")
        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()
        self._sublayout = QtWidgets.QHBoxLayout()

        self._textBrowser = QtWidgets.QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._textBrowser.setTextColor(self.palette().color(QPalette.WindowText))
        self._layout.addWidget(self._textBrowser)

        self._textbox = QtWidgets.QLineEdit()
        self._sublayout.addWidget(self._textbox)
        self._decoder = QtWidgets.QComboBox()
        for mode in self._encodings:
            self._decoder.addItem(mode)
        self._sublayout.addWidget(self._decoder)

        self._hist_button = QtWidgets.QPushButton()
        self._hist_button.setIcon(QIcon(os.path.expanduser("~") + '/.binaryninja/plugins/binja_voltron_toolbar/icons/history.png'))
        self._hist_button.setIconSize(QSize(22, 22))

        self.history = []
        self._hist_menu = QtWidgets.QMenu()
        self._hist_menu.addAction("Clear History", self.clear_history)
        self._hist_menu.insertSection(self._hist_menu.actions()[0], "---------")
        self._hist_menu.setTearOffEnabled(True)
        self._hist_button.setMenu(self._hist_menu)

        self._sublayout.addWidget(self._hist_button)
        self._layout.addLayout(self._sublayout)

        self._messages = Queue()
        self._pty_thread = TerminalThread(self._messages)
        self._pty_thread.RECV_LINE.connect(self.recv_line)
        self._pty_thread.start()

        self._textbox.returnPressed.connect(self.submit_line)

        self.resize(self.width(), int(self.height() * 0.5))

        self.setObjectName('Terminal_Window')

    def _autoscroll(self):
        self._textBrowser.moveCursor(QTextCursor.End)
        self._textBrowser.ensureCursorVisible()

    def recv_line(self, line):
        self._textBrowser.insertPlainText(line)
        self._autoscroll()

    def submit_line(self):
        raw = self._textbox.text()
        line = self.decode(raw)
        if line is None:
            return
        if raw not in self.history:
            self.history.append(raw)
            action = QtWidgets.QAction(str(raw), self)
            action.triggered.connect(partial(self.set_text_box_contents, raw))
            self._hist_menu.insertAction(self._hist_menu.actions()[0], action)
        self._messages.put((line, None))
        self._textBrowser.setTextColor(usercolor)
        self._textBrowser.insertPlainText(line + "\n")
        self._textBrowser.setTextColor(self.palette().color(QPalette.WindowText))
        self._textbox.clear()
        self._autoscroll()

    @property
    def tty(self):
        return self._pty_thread.tty

    def decode(self, encoded):
        mode = self._encodings[self._decoder.currentIndex()]
        if mode == 'raw':
            return encoded
        try:
            if mode == 'hex':
                return encoded.decode('hex')
            if mode == 'b64':
                return b64decode(encoded)
            if mode == 'py2':
                return eval(encoded)
        except:
            log_alert("Failed to decode input")
            return None

    def clear_history(self):
        self.history = []
        self._hist_menu.clear()
        self._hist_menu.addAction("Clear History", self.clear_history)

    def set_text_box_contents(self, newcontents):
        self._textbox.clear()
        self._textbox.insert(newcontents)
