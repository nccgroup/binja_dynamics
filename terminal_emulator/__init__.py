from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QTextCursor, QIcon, QFontDatabase
from base64 import b64decode

import pty, select, os
from queue import Queue
from functools import partial

from binaryninja import log_alert

usercolor = QColor(255, 153, 51) # Nice orange highlight color

class TerminalThread(QThread):
    """ Helper thread that creates the tty for gdb to redirect input and output
    for the binary to. """
    RECV_LINE = pyqtSignal(str)

    def __init__(self, message_q):
        QThread.__init__(self)
        self.messages = message_q
        # Only the inferior process need use the slave file descriptor
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
                # Expects a message to contain either the string 'exit'
                # or a line of input in a tuple: ('input', None)
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
                # Read when the binary has new output for us (that didn't come from us)
                line = os.read(self.master, 1024) # Reads up to a kilobyte at once. Should this be higher/lower?
                self.RECV_LINE.emit(line)
            if w:
                os.write(self.master, message + "\n")
                self.messages.task_done()
                self.dirty = True # Mark that we've written something to the tty
                                  # so we won't read again until the binary has
                                  # consumed those bytes

class TerminalWindow(QtWidgets.QWidget):
    """ Displays a text browser and a text box that emulate a terminal in which
    the user can interact with the binary. Only supported in GDB because LLDB doesn't
    seem to support tty redirection on linux. Allows the user to enter input in several
    different formats for convenience. Also offers a history feature. """
    def __init__(self):
        super(TerminalWindow, self).__init__()
        # Raw input, decode as hex, decode as base64, evaluate as a python expression
        self._encodings = ['raw', 'hex', 'b64', 'py2']
        self.framelist = []
        self.setWindowTitle("Binary Interaction")
        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()
        self._sublayout = QtWidgets.QHBoxLayout()
        self._statusbar = QtWidgets.QHBoxLayout()

        # Creates the textbrowser for binary output
        self._textBrowser = QtWidgets.QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._textBrowser.setTextColor(self.palette().color(QPalette.WindowText))
        self._textBrowser.textChanged.connect(self.handle_new_output)
        self._textBrowser.selectionChanged.connect(self.handle_selection_changed)
        self._textBrowser.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self._layout.addWidget(self._textBrowser)

        # Creates the textbox for binary input
        self._textbox = QtWidgets.QLineEdit()
        self._textbox.textChanged.connect(self.handle_text_changed)
        self._textbox.cursorPositionChanged.connect(self.handle_cursor_change)
        self._sublayout.addWidget(self._textbox)
        self._decoder = QtWidgets.QComboBox()
        for mode in self._encodings:
            self._decoder.addItem(mode)
        self._sublayout.addWidget(self._decoder)

        # Creates the history button
        self._hist_button = QtWidgets.QPushButton()
        self._hist_button.setIcon(QIcon(os.path.expanduser("~") + '/.binaryninja/plugins/binja_voltron_toolbar/icons/history.png'))
        self._hist_button.setIconSize(QSize(22, 22))

        # We use a submenu to implement the history browser. It's not the prettiest,
        # but it has the perk of already being built-in to Qt
        self.history = []
        self._hist_menu = QtWidgets.QMenu()
        self._hist_menu.addAction("Clear History", self.clear_history)
        self._hist_menu.insertSection(self._hist_menu.actions()[0], "---------")
        self._hist_menu.setTearOffEnabled(True)
        self._hist_button.setMenu(self._hist_menu)

        self._sublayout.addWidget(self._hist_button)
        self._layout.addLayout(self._sublayout)

        # Creates the bottom label that displays the byte counts
        self._leftLabel = QtWidgets.QLabel()
        self._rightLabel = QtWidgets.QLabel()
        self._rightLabel.setAlignment(Qt.AlignRight)
        # Cursor position, line length
        self._leftLabel.setText("0, 0")
        # Selection size, total bytes output, +bytes in last write
        self._rightLabel.setText("0, 0, +0")
        self._statusbar.addWidget(self._leftLabel)
        self._statusbar.addWidget(self._rightLabel)
        self._layout.addLayout(self._statusbar)

        # Create message passing queue, initialize thread, connect incoming lines
        # to text browser
        self._messages = Queue()
        self._pty_thread = TerminalThread(self._messages)
        self._pty_thread.RECV_LINE.connect(self.recv_line)
        self._pty_thread.start()

        self._textbox.returnPressed.connect(self.submit_line)

        self.resize(self.width(), int(self.height() * 0.5))

        self.setObjectName('Terminal_Window')

    def _autoscroll(self):
        """ Sticks to the bottom of the window """
        self._textBrowser.moveCursor(QTextCursor.End)
        self._textBrowser.ensureCursorVisible()

    def recv_line(self, line):
        """ Inserts the line into the browser without any highlighting """
        self._textBrowser.insertPlainText(line)
        self._autoscroll()

    def submit_line(self):
        """ Writes the input to the text browser, adds it to the history, and
        adds it to the message queue to be sent to the binary """
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
        self._autoscroll()
        self._textBrowser.setTextColor(usercolor)
        self._textBrowser.insertPlainText(line + "\n")
        self._textBrowser.setTextColor(self.palette().color(QPalette.WindowText))
        self._textbox.clear()
        self._autoscroll()

    @property
    def tty(self):
        return self._pty_thread.tty

    def decode(self, encoded):
        """ Takes the input from the text box and decodes it using the parameter
        set in the combobox """
        mode = self._encodings[self._decoder.currentIndex()]
        if mode == 'raw':
            return str(encoded)
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
        """ Wipes out the command history """
        self.history = []
        self._hist_menu.clear()
        self._hist_menu.addAction("Clear History", self.clear_history)

    def set_text_box_contents(self, newcontents):
        """ Helper function for the history that places the line clicked in the text box """
        self._textbox.clear()
        self._textbox.insert(newcontents)

    def bring_to_front(self):
        """ Brings the terminal window to the front and places the cursor in the textbox """
        self._textbox.setFocus()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    # Handlers that update the labels at the bottom
    def handle_cursor_change(self, _old, new):
        oldtext = self._leftLabel.text().split(', ')
        self._leftLabel.setText(str(new) + ', ' + oldtext[1])

    def handle_text_changed(self, newText):
        oldtext = self._leftLabel.text().split(', ')
        self._leftLabel.setText(oldtext[0] + ', ' + str(len(newText)))

    def handle_new_output(self):
        oldtext = self._rightLabel.text().split(', +')[0].split(', ')
        oldlen, newlen = int(oldtext[1]), len(self._textBrowser.toPlainText())
        self._rightLabel.setText(oldtext[0] + ', ' + str(newlen) + ', +' + str(newlen-oldlen))

    def handle_selection_changed(self):
        oldtext = self._rightLabel.text().split(', +')[0].split(', ')
        oldR = self._rightLabel.text().split(', +')[1]
        selection = self._textBrowser.textCursor().selectedText()
        self._rightLabel.setText(str(len(selection)) + ', ' + oldtext[1] + ', +'+ oldR)
