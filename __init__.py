from __future__ import print_function
from binja_toolbar import add_image_button, set_bv, add_picker
from binjatron_extensions import run_binary, step_one, step_over, step_out, \
    continue_exec, get_registers, sync, set_breakpoint, get_memory, \
    get_backtrace, register_sync_callback, set_tty, sync_state
from binja_spawn_terminal import spawn_terminal
from collections import OrderedDict
from functools import partial
from time import sleep
import psutil, os

iconsize = (24, 24)

from register_viewer import RegisterWindow
from memory_viewer import MemoryWindow
from traceback_viewer import TracebackWindow
from terminal_emulator import TerminalWindow
from message_box import MessageBox
from binaryninja import PluginCommand, log_info, log_alert, log_error, execute_on_main_thread_and_wait, user_plugin_path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

main_window = None
reglist = []
segments = ['stack', 'bss']
debugger = "gdb -q"
reg_width = 64
reg_prefix = 'r'

def navigate_to_address(bv, address):
    """ Jumps binja to an address, if it's within the scope of the binary. Might
    extend in the future to support jumping the memory viewer to a given address in memory,
    which would be useful for situations where code is executing on the stack."""
    bv.file.navigate(bv.file.view, address)

def init_gui():
    """ Tries to find the main Binja window. If we've already found it, does nothing.
    Call this as many times as you want, just in case. """
    global main_window
    if main_window is None:
        app = QApplication.instance()
        main_window = [x for x in app.allWidgets() if x.__class__ is QMainWindow][0]

def show_message(message):
    """ Originally popped up a message box. Now just logs to console """
    global main_window
    init_gui()
    log_info(message)
    if(hasattr(main_window, 'messagebox')):
        main_window.messagebox.update(message)
    else:
        main_window.messagebox = MessageBox()
        # main_window.messagebox.show()

def show_register_window(bv):
    """ Builds the register window and attaches it to the main window so it won't
    get garbage collected """
    global reglist, main_window
    regs = OrderedDict() # Keep the registers in a sensible order
    # Figures out rip/eip and rflags/eflags for different architectures
    reglist.append(reg_prefix + 'ip')
    regs[reg_prefix + 'ip'] = (0, reg_width)
    reglist.append(reg_prefix + 'flags')
    regs[reg_prefix + 'flags'] = (0, reg_width)
    # Strips most of less-commonly-used registers. Nothing wrong with removing the filter
    # if you want to see them. It'll just make the register window a lot bigger.
    for reg in filter(lambda x: 'mm' not in x and 'st' not in x and 'base' not in x, bv.arch.full_width_regs):
        regs[reg] = (0, bv.arch.regs[reg].size * 8)
        reglist.append(reg)

    # Attach register window to main window
    init_gui()
    main_window.regwindow = RegisterWindow()
    main_window.regwindow.update_registers(regs)
    main_window.regwindow.show()

def show_memory_window(_bv):
    """ Builds an empty memory viewer and attaches it to the main window """
    global main_window
    init_gui()
    main_window.hexv = MemoryWindow(OrderedDict([(segname, 0x0) for segname in segments]))
    main_window.hexv.show()

def show_traceback_window(bv):
    """ Builds the traceback viewer with sample frames. Sets the handlers to the navigate_to_address function"""
    global main_window
    init_gui()
    main_window.tb_window = TracebackWindow()
    main_window.tb_window.update_frames([{'index': 0, 'addr': 0, 'name': 'None'}])
    main_window.tb_window.update_ret_address(0x0)
    main_window.tb_window.set_button_handler(partial(navigate_to_address, bv))
    main_window.tb_window.set_hyperlink_handler(lambda addr: navigate_to_address(bv, int(addr.toString())))
    main_window.tb_window.show()

def show_terminal_window(bv):
    """ Builds empty terminal window and attaches it to the main window """
    global main_window
    init_gui()
    main_window.term_window = TerminalWindow()
    main_window.term_window.show()

def update_registers(registers, derefs):
    """ Updates the value and dereference string for each register in the OrderedDict
    passed in the registers parameter. """
    global main_window
    if main_window is not None:
        dereferences = OrderedDict()
        if(len(registers.keys()) == 0):
            log_alert("Got a response from Voltron, but no registers. The process has probably exited.")
            return
        # Update registers in order, build an OrderedDict of derefs so the order
        # for those is preserved too.
        for reg in reglist:
            try:
                main_window.regwindow.update_single_register(reg, registers[reg])
                dereferences[reg] = derefs[reg]
            except KeyError:
                log_error("Voltron did not return a register called " + reg)
        main_window.regwindow.update_derefs(dereferences)
        main_window.regwindow.highlight_dirty()

def signal_sync_done(bv, _results):
    """ Callback designed to run the update_wrapper function again immediately after we've had our first successful sync
    after being unable to succesfully sync. Has to run on the main thread to prevent a crash. The outer lambda function
    calls the update wrapper, while the inner lambda function acts as a stub so that wrapped() doesn't fail. """
    execute_on_main_thread_and_wait(lambda: update_wrapper(lambda _: log_info("Called update wrapper within callback"), bv))

import pprint as pp
def update_wrapper(wrapped, bv):
    """ Runs each time a button on the toolbar is pushed. Updates the live displays of program information """
    # Call wrapped function
    wrapped(bv)
    # Handle Register Updates
    reg, derefs = get_registers(bv) # derefs will have the error message if something goes wrong
    try:
        update_registers(reg, derefs)
    except AttributeError: # reg was None
        if(derefs == 'Target busy'):  # Probably living in kernel-land, which could be for a number of reasons.
            # We make the hopeful assumption that the reason is the program is waiting for user input.
            main_window.term_window.bring_to_front()
            log_info("The target was busy, preventing us from retrieving the register state. It may be waiting for input from you.")
        elif(derefs == 'No such target'):
            # Usually happens when the inferior process has exited
            log_alert("Couldn't get register state. The process may not be running.")
        else:
            # Maybe you didn't run the binary yet?
            log_alert("Couldn't get register state. Please consult the log for more information")
        # If something went wrong with the last update, we register a callback that will get run
        # the next time we have a sucessful sync. We partially apply the arguments on the callback
        # so we don't lose our reference to the binary view. See docstring on signal_sync_done for more
        register_sync_callback(partial(signal_sync_done, bv), should_delete=True)
        return
    # Handle Memory Updates
    procname = bv.file.filename.split("/")[-1].replace(".bndb","")
    # Iterate through the processes on the system to find the right memory map
    for proc in psutil.process_iter():
        if proc.name() == procname: # Found debugged process
            maps = proc.memory_maps(grouped=False)
            for m in maps:
                # Update Stack
                if(m.path.strip("[]") == 'stack'):
                    addr = m.addr.split("-")
                    high = int(addr[1],16)
                    sp, bp, ip = reg[reg_prefix + 'sp'], reg[reg_prefix + 'bp'], reg[reg_prefix + 'ip']
                    # Lock out the top of the memory to an even multiple of 32 so we don't
                    # get confusing column-wise shifts in the display
                    memtop = sp if (sp % 32 == 0) else (sp + (32 - sp % 32) - 32)
                    mem = get_memory(bv, memtop, high-memtop)
                    if mem is None:
                        log_error("No memory returned!")
                        return
                    # Display memory from the base of the stack (high addresses)
                    # to the stack pointer (low addresses)
                    main_window.hexv.update_display('stack', memtop, mem)
                    main_window.hexv.highlight_stack_pointer(sp, width=reg_width/8)
                    main_window.hexv.highlight_base_pointer(bp, width=reg_width/8)

                    if (ip > memtop and ip <= high):
                        main_window.hexv.highlight_instr_pointer(ip)

                    # Update BSS
                    try:
                        bss = bv.sections['.bss']
                        bssmem = get_memory(bv, bss.start, bss.length)
                        main_window.hexv.update_display('bss', bss.start, bssmem)
                    except KeyError:
                        log_info('Binary has no bss section')

                    # Repaint the viewer once (much faster than the 8 times we used to do)
                    main_window.hexv.redraw()

                    # Update traceback
                    main_window.tb_window.update_frames(get_backtrace(bv))
                    ret_add_loc = bp - memtop + (reg_width/8)
                    # Grab the saved return address from the stack
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
    """ Does first time setup for everything. See show_message calls for more explanation.
    Not sure how well this handles being called twice... """
    global main_window, reg_prefix, reg_width
    if(bv.arch.name == 'x86_64'):
        pass
    elif(bv.arch.name == 'x86'):
        reg_width = 32
        reg_prefix = 'e'
    else:
        log_error("Architecture not supported!") # Maybe msp430 someday?

    show_message("Syncing with Voltron")
    if not sync(bv):
        show_message("Could not Sync with Voltron, spawning debugger terminal")
        terminal_wrapper(bv)
        for _ in range(5): # Give up if the sync doesn't work after five seconds
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
    # Set the binary view the toolbar should pass to everything it calls
    set_bv(bv)
    show_register_window(bv)
    show_memory_window(bv)
    show_traceback_window(bv)
    if('gdb' in debugger):
        show_terminal_window(bv)
        # Tell GDB to hand off io from the binary to our pseudoterminal
        set_tty(bv, main_window.term_window.tty)
    main_window.messagebox.hide()

def picker_callback(x):
    """ Swaps out the debugger if the combobox on the toolbar is used"""
    global debugger
    debugger = "lldb" if (x == 1) else "gdb -q"

def terminal_wrapper(bv):
    """ Makes sure we set the tty correctly if we have to spawn a new gdb window """
    spawn_terminal(debugger + " " + bv.file.filename.replace(".bndb",""))
    if hasattr(main_window, 'term_window'):
        if "gdb" in debugger:
            for i in range(5):
                if sync_state():
                    break
                sleep(1)
            set_tty(bv, main_window.term_window.tty)

add_picker(['gdb', 'lldb'], picker_callback)
PluginCommand.register("Enable Dynamic Analysis Tools", "Enables features for dynamic analysis on this binary view", enable_dynamics)
PluginCommand.register("Close All Windows", "Closes the entire application", lambda _bv: QApplication.instance().closeAllWindows())

path = user_plugin_path + '/binja_dynamics/'
add_image_button(path + "icons/terminal.png", iconsize, terminal_wrapper, "Open a terminal with the selected debugger session")
add_image_button(path + "icons/run.png", iconsize, partial(update_wrapper, run_binary), "Run Binary")
add_image_button(path + "icons/stepinto.png", iconsize, partial(update_wrapper, step_one), "Step to next instruction")
add_image_button(path + "icons/stepover.png", iconsize, partial(update_wrapper, step_over), "Step over call instruction")
add_image_button(path + "icons/finish.png", iconsize, partial(update_wrapper, step_out), "Step out of stack frame")
add_image_button(path + "icons/continue.png", iconsize, partial(update_wrapper, continue_exec), "Continue to next breakpoint")
