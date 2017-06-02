from binja_toolbar import add_image_button, set_bv
from binja_spawn_terminal import spawn_terminal
from binjatron import run_binary, step_one, step_over, step_out, continue_exec, get_registers, sync, set_breakpoint
from collections import OrderedDict
from functools import partial
from time import sleep

iconsize = (24, 24)

from register_viewer import Window
from message_box import MessageBox
from binaryninja import PluginCommand, log_info, log_alert
from PyQt5.QtWidgets import QApplication, QMainWindow

main_window = None
reglist = []

def init_gui():
    global main_window
    if main_window is None:
        app = QApplication.instance()
        main_window = [x for x in app.allWidgets() if x.__class__ is QMainWindow][0]

def show_message(message):
    global main_window
    init_gui()
    log_info(message)
    if(hasattr(main_window, 'messagebox')):
        main_window.messagebox.update(message)
    else:
        main_window.messagebox = MessageBox()
        main_window.messagebox.show()

def show_register_window(bv):
    global reglist, main_window
    regs = OrderedDict()
    if(bv.arch.name == 'x86_64'):
        reglist.append('rip')
        regs['rip'] = (0, 64)
    elif(bv.arch.name == 'x86'):
        reglist.append('eip')
        regs['eip'] = (0, 32)
    for reg in filter(lambda x: 'mm' not in x and 'st' not in x and 'base' not in x, bv.arch.full_width_regs):
        regs[reg] = (0, bv.arch.regs[reg].size * 8)
        reglist.append(reg)

    init_gui()
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
            except TypeError:
                log_alert("Couldn't get register state. The process may have exited, or it may be waiting for input from you.")
                break
        main_window.regwindow.highlight_dirty()

def update_wrapper(wrapped, view):
    wrapped(view)
    update_registers(get_registers(view))

def enable_dynamics(view):
    global main_window
    show_message("Placing windows")
    show_register_window(view)
    set_bv(view)
    show_message("Syncing with Voltron")
    if not sync(view):
        show_message("Could not Sync with Voltron, spawning LLDB Terminal")
        spawn_terminal("lldb " + view.file.filename)
        for _ in range(5):
            if(sync(view)):
                break
            sleep(1)
    show_message("Attempting to set breakpoint at main")
    funcs = [f for f in filter(lambda b: b.name == 'main', view.functions)]
    if(len(funcs) != 0):
        set_breakpoint(view, funcs[0].start)
        view.file.navigate(view.file.view, funcs[0].start)
    else:
        show_message("No main function found")
    main_window.messagebox.hide()

PluginCommand.register("Enable Dynamic Analysis Features", "Enables features for dynamic analysis on this binary view", enable_dynamics)
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/terminal.png", iconsize, lambda bv: spawn_terminal("lldb " + bv.file.filename), "Open a terminal with an LLDB Session")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/run.png", iconsize, partial(update_wrapper, run_binary), "Run Binary")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepinto.png", iconsize, partial(update_wrapper, step_one), "Step to next instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepover.png", iconsize, partial(update_wrapper, step_over), "Step over call instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/finish.png", iconsize, partial(update_wrapper, step_out), "Step out of stack frame")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/continue.png", iconsize, partial(update_wrapper, continue_exec), "Continue to next breakpoint")
