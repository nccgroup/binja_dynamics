from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from hexview import HexDisplay
from collections import OrderedDict

class MemoryWindow(QtWidgets.QWidget):
    """
    GUI for displaying a live dump of the memory of an executing binary
    """
    _segments = ['stack', 'bss', 'data']
    segment_starts = None
    display_segment = 'stack'

    def __init__(self, segments=None):
        """
        Initializes GUI components. 
        Takes either no arguments, or a dict containing segment names and starting addresses
        """
        super(MemoryWindow, self).__init__()
        self.setWindowTitle("Memory")
        self.stack_pointer = None
        self.base_pointer = None

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
        # Call change_display_segment whenever the user messes with the combobox
        self._picker.currentIndexChanged.connect(self.change_display_segment)

        # viewstack controls switching between the different segments views
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
        """ Swaps the displayed segment. Takes a segment name or an index."""
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
        """ Returns the index-th hexview in the stack """
        if type(index) is str:
            return self.viewstack.widget(self._segments.index(index))
        if type(index) is int:
            return self.viewstack.widget(index)
        else:
            print("Expected int or str, got " + type(index))
        return None

    def update_display(self, segment, address, new_memory):
        """ Updates the displayed memory. The way this is currently implemented,
        memory should always be pushed to 0x0 and the offset updated manually.
        Any memory at addresses after the end of the new buffer will simply be lost."""
        # print("Got", len(new_memory), "bytes to push to", segment, "at", hex(address))
        self.get_widget(segment).update_addr(0x0, new_memory)
        self.get_widget(segment).set_new_offset(address)

    def highlight_bytes_at_address(self, segment, address, length, color=Qt.red):
        """ Helper function for highlighting """
        self.get_widget(segment).highlight_address(address, length, color)

    def highlight_stack_pointer(self, sp, width=8):
        """ Removes old stack pointer highlights and creates a new one """
        if self.stack_pointer is not None:
            self.get_widget('stack').clear_highlight(self.stack_pointer)
        self.highlight_bytes_at_address('stack', sp, width, QColor(0xA2, 0xD9, 0xAF))
        self.stack_pointer = sp

    def highlight_base_pointer(self, bp, width=8):
        """ Highlights the base pointer, and highlights the memory addresses immediately following
        it, which usually correspond to the return address."""
        # Base Pointer
        if self.base_pointer is not None:
            self.get_widget('stack').clear_highlight(self.base_pointer)
        self.highlight_bytes_at_address('stack', bp, width, Qt.darkYellow)
        # Return Address
        if self.base_pointer is not None:
            self.get_widget('stack').clear_highlight(self.base_pointer+width)
        if self.base_pointer != self.stack_pointer:
            self.highlight_bytes_at_address('stack', bp+width, width, Qt.darkRed)
        self.base_pointer = bp

    def redraw(self):
        self.get_widget(self._picker.currentIndex()).redraw()
