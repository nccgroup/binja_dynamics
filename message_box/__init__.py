from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QByteArray
from PyQt5 import QtGui

class MessageBox(QtWidgets.QWidget):

    def __init__(self, text="Loading..."):
        super(MessageBox, self).__init__()
        self.setWindowTitle("Messages")
        
        self.setLayout(QtWidgets.QHBoxLayout())
        self._layout = self.layout()

        self._gif = QtWidgets.QLabel()
        movie = QtGui.QMovie("loading.gif")
        self._gif.setMovie(movie)
        movie.start()
        self._layout.addWidget(self._gif)

        self._message = QtWidgets.QLabel()
        self._message.setText(text)
        self._layout.addWidget(self._message)
        self.setObjectName('Message_Window')

    def update(self, newtext):
        self._message.setText(newtext)
