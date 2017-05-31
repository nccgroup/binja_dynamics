from binja_toolbar import add_image_button
from binja_spawn_terminal import spawn_terminal
from binjatron import run_binary, step_one, step_over, step_out, continue_exec
from collections import OrderedDict

iconsize = (24, 24)

add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/terminal.png", iconsize, lambda bv: spawn_terminal("lldb " + bv.file.filename), "Open a terminal with an LLDB Session")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/run.png", iconsize, run_binary, "Run Binary")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepinto.png", iconsize, step_one, "Step to next instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepover.png", iconsize, step_over, "Step over call instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/finish.png", iconsize, step_out, "Step out of stack frame")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/continue.png", iconsize, continue_exec, "Continue to next breakpoint")

from register_viewer import Window
from binaryninja import PluginCommand
from PyQt5.QtWidgets import QApplication, QMainWindow

def show_register_window(bv):
    regs = OrderedDict()
    for reg in bv.arch.full_width_regs:
        regs[reg] = 0

    app = QApplication.instance()
    main_window = [x for x in app.allWidgets() if x.__class__ is QMainWindow][0]
    main_window.regwindow = Window()
    print("Updating Registers")
    main_window.regwindow.update_registers(regs)
    main_window.regwindow.show()
    print("Complete")

PluginCommand.register("Show Register Window", "", show_register_window)
