from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

import pty, select, os
from queue import Queue

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
                print("Writing Message")
                print(message)
                os.write(self.master, message + "\n")
                self.messages.task_done()
                self.dirty = True

class TerminalWindow(QtWidgets.QWidget):

    def __init__(self):
        super(TerminalWindow, self).__init__()
        self.framelist = []
        self.setWindowTitle("Binary Interaction")
        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._textBrowser = QtWidgets.QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._layout.addWidget(self._textBrowser)

        self._textbox = QtWidgets.QLineEdit()
        self._layout.addWidget(self._textbox)

        self._messages = Queue()
        self._pty_thread = TerminalThread(self._messages)
        self._pty_thread.RECV_LINE.connect(self.recv_line)
        self._pty_thread.start()

        self._textbox.returnPressed.connect(self.submit_line)

        self.resize(self.width(), int(self.height() * 0.5))

        self.setObjectName('Terminal_Window')

    def recv_line(self, line):
        self._textBrowser.insertPlainText(line)

    def submit_line(self):
        line = self._textbox.text()
        self._messages.put((line, None))
        self._textbox.clear()
