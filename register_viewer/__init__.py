from __future__ import print_function
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontDatabase, QColor, QBrush
from collections import OrderedDict

monospace = QFontDatabase.systemFont(QFontDatabase.FixedFont)
highlight = QBrush(QColor(255, 153, 51))
default = QBrush(QColor(255, 255, 255))
# Most of the flag parsing code was pinched from the Voltron repo
flagbits = OrderedDict([('c', 0), ('p', 2), ('a', 4), ('z', 6), ('s', 7), ('t', 8), ('i', 9), ('d', 10), ('o', 11)])
flagnames = ["Carry Flag", "Parity Flag", "Adjust Flag", "Zero Flag", "Sign Flag", "Trap Flag", "Interrupt Enable Flag", "Direction Flag", "Overflow Flag"]

def _chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]

def _makewidget(val, center=False):
    """ Small helper function that builds a TableWidgetItem and sets up the font the way we want"""
    out = QtWidgets.QTableWidgetItem(str(val))
    out.setFlags(Qt.ItemIsEnabled)
    out.setFont(monospace)
    if(center):
        out.setTextAlignment(Qt.AlignCenter)
    return out

def parse_flag_register(flagsval):
    """ Borrowed Snare's code for parsing the eflags/rflags register """
    values = OrderedDict()
    for flag in flagbits:
        values[flag] = (flagsval & (1 << flagbits[flag]) > 0)
    return values

class RegisterWindow(QtWidgets.QWidget):
    """ GUI for displaying a live dump of the contents of the registers in various formats."""
    _display_modes = ['binary', 'decimal', 'hex', 'ascii', 'deref']
    registers = OrderedDict()
    display_mode = 'hex'

    def __init__(self, registers=None):
        super(RegisterWindow, self).__init__()
        self.setWindowTitle("Registers")
        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        # Set up display mode combobox
        self._picker = QtWidgets.QComboBox()
        for mode in self._display_modes:
            self._picker.addItem(mode)
        self._picker.setCurrentIndex(2)
        self._layout.addWidget(self._picker)
        self._picker.currentIndexChanged.connect(self.change_display_mode)

        # Set up register table
        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(['Register', 'Value'])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._layout.addWidget(self._table)

        # Set up flag viewer
        self._flags = QtWidgets.QTableWidget()
        self._flags.setColumnCount(len(flagbits.keys()))
        self._flags.setHorizontalHeaderLabels(flagbits.keys())
        self._flags.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._flags.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self._flags.verticalHeader().setVisible(False)
        self._flags.setMaximumHeight(55)
        self._flags.setRowCount(1)
        for index, value in enumerate(flagnames):
            self._flags.horizontalHeaderItem(index).setToolTip(value)
        self._layout.addWidget(self._flags)

        self.setObjectName('Register_Window')

        self.should_clean = False

        if registers is not None:
            self.update_registers(registers)

    def update_registers(self, registers):
        """ Takes a dict of registers - 'name' : (value, width). Mostly just a wrapper around update_single_registers"""
        self._table.setRowCount(len(registers))
        for register in registers:
            self.update_single_register(register, registers[register][0], registers[register][1])
        self.resize(QSize(self._layout.sizeHint().width(), self._table.viewportSizeHint().height() + self._picker.sizeHint().height() + self._table.sizeHint().height()))

    def update_single_register(self, name, value, width=32):
        """ Updates a single register (and adds it if it doesn't exist). Cleans registers if dirty values have been highlighted"""
        if(self.should_clean):
            for reg in self.registers:
                self.registers[reg].dirty = False
        if name not in self.registers.keys():
            self.registers[name] = Register(name, len(self.registers.keys()), width, value)
            self._update_table_entry(name)
        else:
            if self.registers[name].value != value:
                self.registers[name].setval(value)
                self._update_table_entry(name)
        if name == 'eflags' or name == 'rflags':
            self._update_flag_display(value)
        self.should_clean = False

    def _update_table_entry(self, name):
        """ Replaces the table widgets for a given register."""
        self._table.setItem(self.registers[name].index, 0, _makewidget(self.registers[name].name))
        # Passes the display mode to regsiter.getitem
        self._table.setItem(self.registers[name].index, 1, _makewidget(self.registers[name][self.display_mode]))

    def _update_flag_display(self, value):
        """ Handles dirty flag highlighting and updates in general. This is simpler than the register
        highlighting, which is why it thinks all the flags need to be highlighted when first launched."""
        values = parse_flag_register(value)
        for i in range(len(flagbits.keys())):
            oldval = self._flags.item(0, i)
            if oldval is not None:
                oldval = oldval.text()
            self._flags.setItem(0, i, _makewidget("1" if (values[values.keys()[i]]) else "0", True))
            if self._flags.item(0, i).text() != oldval:
                self._flags.item(0, i).setForeground(highlight)
            else:
                self._flags.item(0, i).setForeground(default)

    def change_display_mode(self, mode):
        """ Changes the way register values are decoded. Default is as hexadecimal, but
        also supports integer, binary, ascii, and dereferencing the register value
        as a pointer (thanks voltron!)"""
        if type(mode) is int:
            if (mode < 0) or (mode >= len(self._display_modes)):
                print("Mode index out of range")
                return
            mode = self._display_modes[mode]
        if mode not in self._display_modes:
            print(str(mode) + " is not a valid display mode! Valid modes are: " + str(self._display_modes))
            return
        self.display_mode = mode
        for name in self.registers.keys():
            self._update_table_entry(name)
        self.should_clean = False
        self.highlight_dirty()

    def highlight_dirty(self):
        """ Highlights any registers that have been marked as dirty, and indicates that
        all registers should be cleaned next time the values are updated (Note: NOT the next
        time the display mode is changed)"""
        for reg in self.registers:
            reg = self.registers[reg]
            if(reg.dirty):
                t_item = self._table.item(reg.index, 1)
                if t_item is not None:
                    t_item.setForeground(highlight)
                if(self.should_clean):
                    reg.dirty = False
            else:
                t_item = self._table.item(reg.index, 1)
                if t_item is not None:
                    t_item.setForeground(default)
        self.should_clean = True

    def update_derefs(self, derefs):
        """ Updates dereference values for each register. Necessary because
        derefs are stored separately from values (not pulled live)"""
        for reg in derefs.keys():
            if self.registers[reg].dereference != derefs[reg]:
                self.registers[reg].dereference = derefs[reg]
                # if self.display_mode == 'deref':
                self._update_table_entry(reg)

class Register():
    def __init__(self, name, index, width, value=0):
        self.name = name
        self.bitwidth = width
        self.value = value
        self.index = index
        self.dirty = False
        self.dereference = []

    def __getitem__(self, encoding):
        # If you want to add a new encoding, you'll need to also add it here
        if encoding == 'hex':
            return self.hex
        if encoding == 'decimal':
            return self.decimal
        if encoding == 'binary':
            return self.binary
        if encoding == 'ascii':
            return self.ascii
        if encoding == 'deref':
            return self.deref
        return None

    def __repr__(self):
        return self.name + " (" + str(self.bitwidth) + "b): " + self.hex

    @property
    def binary(self):
        base = bin(self.value)[2:]
        out = '0' * (self.bitwidth - len(base)) + base
        return ' '.join([chunk for chunk in _chunks(out, 8)])

    @property
    def decimal(self):
        """ Registers are stored as decimal by default, so that's how they should
        be passed to setval """
        return self.value

    @property
    def hex(self):
        base = hex(self.value).replace("L","")
        out = "0x" + "0"*((self.bitwidth / 4) - len(base.split('0x')[1])) + base.split('0x')[1]
        return out

    @property
    def ascii(self):
        hexstr = self.hex[2:]
        return "".join([('.' if (int(c, 16) < 32 or int(c, 16) >= 127) else chr(int(c, 16))) for c in _chunks(hexstr, 2)])

    @property
    def deref(self):
        if len(self.dereference) > 0:
            # Voltron gives us an array of the values in sequence
            return " --> ".join((hex(item[1]) if (item[0] == 'pointer') else \
            (item[1] if (item[0] != 'string') else "\"" + item[1] \
            .replace("\n","\\n").replace("\t","\\t") + "\"")) for item in self.dereference[1:])
        return ""

    def setval(self, newval):
        """ Changes the register value and marks it as having changed since the last cleaning """
        self.value = int(newval)
        self.dirty = True
