from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from hexview import HexDisplay
from collections import OrderedDict

class MemoryWindow(QtWidgets.QWidget):
    _segments = ['stack', 'bss', 'data']
    segment_starts = None
    display_segment = 'stack'

    def __init__(self, segments=None):
        """
        Takes either no arguments, or a dict containing segment names and
        """
        super(MemoryWindow, self).__init__()

        if segments is not None:
            if type(segments) is not OrderedDict:
                print("Error: Use collections.OrderedDict instead of dict for segment list")
            self._segments = segments.keys()
            self.segment_starts = segments

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._picker = QtWidgets.QComboBox()
        for segment in self._segments:
            self._picker.addItem(segment)
        self._layout.addWidget(self._picker)
        self._picker.currentIndexChanged.connect(self.change_display_segment)

        self.viewstack = QtWidgets.QStackedWidget()
        for segment in self._segments:
            if self.segment_starts is None:
                disp = HexDisplay()
                disp.update_addr(0, "This is the " + segment + " segment")
            else:
                disp = HexDisplay(starting_address=self.segment_starts[segment])
            self.viewstack.addWidget(disp)

        self._layout.addWidget(self.viewstack)
        self.setMaximumWidth(self.viewstack.widget(0).maximumWidth() + 20)
        self.setMinimumWidth(self.viewstack.widget(0).minimumWidth() + 20)
        self.setObjectName('Memory_Window')

    def change_display_segment(self, segment):
        if type(segment) is int:
            if (segment < 0) or (segment >= len(self._segments)):
                print("segment index out of range")
                return
            segment = self._segments[segment]
        if segment not in self._segments:
            print(str(segment) + " is not a valid display segment! Valid segments are: " + str(self._segments))
            return
        self.display_segment = segment
        self.viewstack.setCurrentIndex(self._segments.index(segment))

    def get_widget(self, index):
        if type(index) is str:
            return self.viewstack.widget(self._segments.index(index))
        if type(index) is int:
            return self.viewstack.widget(index)
        else:
            print("Expected int or str, got " + type(index))
        return None

    def update_display(self, segment, address, new_memory):
        print("Got", len(new_memory), "bytes to push to", segment, "at", address)
        self.get_widget(segment).update_addr(0x0, new_memory)
        self.get_widget(segment).set_new_offset(address)

    def highlight_bytes_at_address(self, segment, address, length):
        self.get_widget(segment).highlight_address(address, length)
