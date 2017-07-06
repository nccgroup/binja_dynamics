import binjatron
from binaryninja import log_error

# Most of this module is undocumented, but hopefully the function names and inline strings
# will make the functionality fairly clear. This module serves as a wrapper around the functions
# exported by binjatron that allow us to get a lot more functionality in terms of interaction
# with Voltron, but without having to modify Binjatron itself.

def _build_command_dict(cmd):
    return {"command": cmd, "block": False}

def get_version(_view):
    return binjatron.custom_request("version", {})

def run_binary(_view):
    binjatron.custom_request("command", _build_command_dict("run"))

def step_one(_view):
    binjatron.custom_request("command", _build_command_dict("si"))

def step_over(_view):
    binjatron.custom_request("command", _build_command_dict("ni"))

def step_out(_view):
    binjatron.custom_request("command", _build_command_dict("finish"))

def continue_exec(_view):
    binjatron.custom_request("command", _build_command_dict("continue"))

def set_tty(_view, tty):
    version = get_version(_view).host_version
    if 'gdb' in version:
        binjatron.custom_request("command", _build_command_dict("tty " + tty))
    elif 'lldb' in version:
        binjatron.custom_request("command", _build_command_dict("settings set target.input-path " + tty))
        binjatron.custom_request("command", _build_command_dict("settings set target.output-path " + tty))

def get_registers(_view):
    res = binjatron.custom_request("registers", {"block":False, "deref":True}, alert=False)
    if(res.is_error):
        log_error("Could not get registers!" + " -- " + res.message)
        return None, res.message
    return res.registers, res.deref

def get_memory(_view, address, length):
    res = binjatron.custom_request("memory", {"block":False, "address":address, "length":length}, alert=False)
    if(res.is_error):
        log_error("Could not get memory at address ``" + str(address) + " -- " + res.message)
        return None
    return res.memory

def get_backtrace(_view):
    try:
        res = binjatron.custom_request("backtrace", {"block:":False}, alert=False)
    except:
        import traceback
        traceback.print_exc()
        log_error("Voltron encountered an exception while getting the backtrace. Maybe this is a stripped binary?")
        return [{'index': 0, 'addr': 0, 'name': 'Exception! Voltron Bug?'}]
    if(res.is_error):
        log_error("Could not get backtrace -- " + res.message)
        return None
    return res.frames

def sync(bv):
    binjatron.sync(bv)
    return binjatron.sync_state()

set_breakpoint = binjatron.set_breakpoint
register_sync_callback = binjatron.register_sync_callback
sync_state = binjatron.sync_state
