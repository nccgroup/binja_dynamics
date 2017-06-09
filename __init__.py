from __future__ import print_function
from binja_toolbar import add_image_button, set_bv, add_picker
from binja_spawn_terminal import spawn_terminal
from binjatron import run_binary, step_one, step_over, step_out, continue_exec, get_registers, sync, set_breakpoint, get_memory, get_backtrace
from collections import OrderedDict
from functools import partial
from time import sleep
import psutil

iconsize = (24, 24)

from register_viewer import RegisterWindow
from memory_viewer import MemoryWindow
from traceback_viewer import TracebackWindow
from message_box import MessageBox
from binaryninja import PluginCommand, log_info, log_alert, log_error
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

main_window = None
reglist = []
segments = ['stack']
debugger = "lldb"
reg_width = 64
reg_prefix = 'r'

def navigate_to_address(bv, address):
    bv.file.navigate(bv.file.view, address)

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
        # main_window.messagebox.show()

def show_register_window(bv):
    global reglist, main_window
    regs = OrderedDict()
    reglist.append(reg_prefix + 'ip')
    regs[reg_prefix + 'ip'] = (0, reg_width)
    reglist.append(reg_prefix + 'flags')
    regs[reg_prefix + 'flags'] = (0, reg_width)
    for reg in filter(lambda x: 'mm' not in x and 'st' not in x and 'base' not in x, bv.arch.full_width_regs):
        regs[reg] = (0, bv.arch.regs[reg].size * 8)
        reglist.append(reg)

    init_gui()
    main_window.regwindow = RegisterWindow()
    main_window.regwindow.update_registers(regs)
    main_window.regwindow.show()

def show_memory_window(_bv):
    global main_window
    init_gui()
    main_window.hexv = MemoryWindow(OrderedDict([(segname, 0x0) for segname in segments]))
    main_window.hexv.show()

def show_traceback_window(bv):
    global main_window
    init_gui()
    main_window.tb_window = TracebackWindow()
    main_window.tb_window.update_frames([{'index': 0, 'addr': 0, 'name': 'No traceback yet'}])
    main_window.tb_window.update_ret_address(0x0)
    main_window.tb_window.set_button_handler(partial(navigate_to_address, bv))
    main_window.tb_window.set_hyperlink_handler(lambda addr: navigate_to_address(bv, int(addr.toString())))
    main_window.tb_window.show()

def update_registers(registers, derefs):
    global main_window
    if main_window is not None:
        dereferences = OrderedDict()
        for reg in reglist:
            try:
                main_window.regwindow.update_single_register(reg, registers[reg])
                dereferences[reg] = derefs[reg]
            except KeyError:
                log_error("Voltron did not return a register called " + reg)
        main_window.regwindow.update_derefs(dereferences)
        main_window.regwindow.highlight_dirty()

import pprint as pp
def update_wrapper(wrapped, bv):
    wrapped(bv)
    try:
        reg, derefs = get_registers(bv)
        update_registers(reg, derefs)
    except TypeError:
        log_alert("Couldn't get register state. The process may not be running, or it may be waiting for input from you.")
        return
    procname = bv.file.filename.split("/")[-1].replace(".bndb","")
    for proc in psutil.process_iter():
        if proc.name() == procname:
            maps = proc.memory_maps(grouped=False)
            for m in maps:
                if(m.path.strip("[]") == 'stack'):
                    addr = m.addr.split("-")
                    high = int(addr[1],16)
                    sp, bp = reg[reg_prefix + 'sp'], reg[reg_prefix + 'bp']
                    memtop = sp if (sp % 32 == 0) else (sp + (32 - sp % 32) - 32)
                    mem = get_memory(bv, memtop, high-memtop)
                    if mem is None:
                        log_error("No memory returned!")
                        return
                    main_window.hexv.update_display('stack', memtop, mem)
                    main_window.hexv.highlight_stack_pointer(sp, width=reg_width/8)
                    main_window.hexv.highlight_base_pointer(bp, width=reg_width/8)
                    main_window.tb_window.update_frames(get_backtrace(bv))
                    ret_add_loc = bp - memtop + 8
                    try:
                        retrieved = mem[ret_add_loc:ret_add_loc + (reg_width/8)][::-1].encode('hex')
                        if(len(retrieved) > 0):
                            ret_add = int(retrieved, 16)
                            main_window.tb_window.update_ret_address(ret_add)
                    except ValueError:
                        log_error("Tried to find the return address before the stack was set up. Carry on.")
                    break
            break

def enable_dynamics(bv):
    global main_window, reg_prefix, reg_width
    if(bv.arch.name == 'x86_64'):
        pass
    elif(bv.arch.name == 'x86'):
        reg_width = 32
        reg_prefix = 'e'
    else:
        log_error("Architecture not supported!")

    show_message("Syncing with Voltron")
    if not sync(bv):
        show_message("Could not Sync with Voltron, spawning debugger terminal")
        spawn_terminal(debugger + " " + bv.file.filename.replace(".bndb",""))
        for _ in range(5):
            if(sync(bv)):
                break
            sleep(1)
    show_message("Attempting to set breakpoint at main")
    funcs = [f for f in filter(lambda b: b.name == 'main', bv.functions)]
    if(len(funcs) != 0):
        set_breakpoint(bv, funcs[0].start)
        navigate_to_address(bv, funcs[0].start)
    else:
        log_alert("No main function found, so no breakpoints were set")
    show_message("Placing windows")
    set_bv(bv)
    show_register_window(bv)
    show_memory_window(bv)
    show_traceback_window(bv)
    main_window.messagebox.hide()

def picker_callback(x):
    global debugger
    debugger = "gdb" if (x == 1) else "lldb"

add_picker(['lldb', 'gdb'], picker_callback)
PluginCommand.register("Enable Dynamic Analysis Features", "Enables features for dynamic analysis on this binary view", enable_dynamics)
PluginCommand.register("Close All Windows", "Closes the entire application", lambda _bv: QApplication.instance().closeAllWindows())
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/terminal.png", iconsize, lambda bv: spawn_terminal(debugger + " " + bv.file.filename), "Open a terminal with the selected debugger session")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/run.png", iconsize, partial(update_wrapper, run_binary), "Run Binary")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepinto.png", iconsize, partial(update_wrapper, step_one), "Step to next instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepover.png", iconsize, partial(update_wrapper, step_over), "Step over call instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/finish.png", iconsize, partial(update_wrapper, step_out), "Step out of stack frame")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/continue.png", iconsize, partial(update_wrapper, continue_exec), "Continue to next breakpoint")
