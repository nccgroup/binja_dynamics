from binja_toolbar import add_image_button
from binja_spawn_terminal import spawn_terminal
from binjatron import run_binary, step_one, step_over, step_out, continue_exec, get_registers
from collections import OrderedDict
from functools import partial

iconsize = (24, 24)

from register_viewer import Window
from binaryninja import PluginCommand
from PyQt5.QtWidgets import QApplication, QMainWindow

main_window = None
reglist = []

def show_register_window(bv):
    global reglist, main_window
    regs = OrderedDict()
    for reg in filter(lambda x: 'mm' not in x and 'st' not in x and 'base' not in x, bv.arch.full_width_regs):
        regs[reg] = (0, bv.arch.regs[reg].size * 8)
        reglist.append(reg)

    app = QApplication.instance()
    main_window = [x for x in app.allWidgets() if x.__class__ is QMainWindow][0]
    main_window.regwindow = Window()
    main_window.regwindow.update_registers(regs)
    main_window.regwindow.show()

def update_registers(registers):
    global main_window
    if main_window is not None:
        print("Updating Registers")
        for reg in reglist:
            try:
                main_window.regwindow.update_single_register(reg, registers[reg])
            except KeyError:
                print("Voltron did not return a register called " + reg)
        main_window.regwindow.highlight_dirty()

def update_wrapper(wrapped, view):
    wrapped(view)
    update_registers(get_registers(view))

PluginCommand.register("Show Register Window", "", show_register_window)
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/terminal.png", iconsize, lambda bv: spawn_terminal("lldb " + bv.file.filename), "Open a terminal with an LLDB Session")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/run.png", iconsize, run_binary, "Run Binary")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepinto.png", iconsize, partial(update_wrapper, step_one), "Step to next instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepover.png", iconsize, partial(update_wrapper, step_over), "Step over call instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/finish.png", iconsize, partial(update_wrapper, step_out), "Step out of stack frame")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/continue.png", iconsize, continue_exec, "Continue to next breakpoint")
