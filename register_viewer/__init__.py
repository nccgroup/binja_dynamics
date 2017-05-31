from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase
from collections import OrderedDict

monospace = QFontDatabase.systemFont(QFontDatabase.FixedFont)

def _makewidget(val):
    out = QtWidgets.QTableWidgetItem(str(val))
    out.setFlags(Qt.ItemIsEnabled)
    out.setFont(monospace)
    return out

class Window(QtWidgets.QWidget):
    _display_modes = ['binary', 'decimal', 'hex', 'ascii']
    registers = OrderedDict()
    display_mode = 'hex'

    def __init__(self, registers=None):
        super(Window, self).__init__()

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._picker = QtWidgets.QComboBox()
        for mode in self._display_modes:
            self._picker.addItem(mode)
        self._layout.addWidget(self._picker)
        self._picker.currentIndexChanged.connect(self.change_display_mode)

        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(['Register', 'Value'])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._layout.addWidget(self._table)

        self.setObjectName('Register_Window')

        if registers is not None:
            self.update_registers(registers)

    def update_registers(self, registers):
        self._table.setRowCount(len(registers))
        for register in registers:
            self.update_single_register(register, registers[register])

    def update_single_register(self, name, value):
        if name not in self.registers.keys():
            self.registers[name] = Register(name, len(self.registers.keys()), value)
        else:
            self.registers[name].value = value
        self._table.setItem(self.registers[name].index, 0, _makewidget(self.registers[name].name))
        self._table.setItem(self.registers[name].index, 1, _makewidget(self.registers[name].hex))

    def change_display_mode(self, mode):
        if type(mode) is int:
            if (mode < 0) or (mode >= len(self._display_modes)):
                print("Mode index out of range")
                return
            mode = self._display_modes[mode]
        if mode not in self._display_modes:
            print(str(mode) + " is not a valid display mode! Valid modes are: " + str(self._display_modes))
            return
        print("Not yet implemented!")


class Register():
    def __init__(self, name, index, value=0x0):
        self.name = name
        self.value = value
        self.index = index

    @property
    def binary(self):
        return "0"

    @property
    def decimal(self):
        return 0

    @property
    def hex(self):
        return "0x0"

    @property
    def ascii(self):
        return ""
