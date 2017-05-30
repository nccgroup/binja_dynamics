from binja_toolbar import add_image_button
from binja_spawn_terminal import spawn_terminal

def term_wrapper(bv):
    spawn_terminal("lldb " + bv.file.filename)

def not_implemented(_bv):
    print("Not implemented!")

add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/terminal.png", (32,32), term_wrapper, "Open a terminal with an LLDB Session")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/run.png", (32,32), not_implemented, "Run Binary")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepinto.png", (32,32), not_implemented, "Step to next instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stepover.png", (32,32), not_implemented, "Step over call instruction")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/continue.png", (32,32), not_implemented, "Continue to next breakpoint")
add_image_button(".binaryninja/plugins/binja_voltron_toolbar/icons/stop.png", (32,32), not_implemented, "Stop the binary")
