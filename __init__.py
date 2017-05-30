from binja_toolbar import add_image_button
from binja_spawn_terminal import spawn_terminal
from binjatron import run_binary, step_one, step_over, step_out, continue_exec

iconsize = (24, 24)

add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/terminal.png", iconsize, lambda bv: spawn_terminal("lldb " + bv.file.filename), "Open a terminal with an LLDB Session")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/run.png", iconsize, run_binary, "Run Binary")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepinto.png", iconsize, step_one, "Step to next instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepover.png", iconsize, step_over, "Step over call instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/finish.png", iconsize, step_out, "Step out of stack frame")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/continue.png", iconsize, continue_exec, "Continue to next breakpoint")
