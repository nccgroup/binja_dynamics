from binaryninja import ChoiceField, SeparatorField, TextLineField, get_form_input, log_alert
from base64 import b64decode
import struct

choices = ['raw', 'hex', 'b64', 'py2']

def get_debugger_argument(bv):
    """ Pops up a window that lets the user set the debugger arguments. Implemented
    using the native Binja GUI, so we don't have the option of showing a command history"""
    mode = ChoiceField("Mode", choices)
    text = TextLineField("")

    get_form_input([mode, SeparatorField(), text], "Set Run Arguments")

    if mode.result is None:
        mode = 'raw'
    else:
        mode = mode.choices[mode.result]
    text = str(text.result).strip()

    if mode == 'raw':
        return text
    try:
        if mode == 'hex':
            return text.decode('hex')
        if mode == 'b64':
            return b64decode(text)
        if mode == 'py2':
            return eval(text)
    except:
        log_alert("Failed to decode input")
        return ""
