import traceback

from binaryninja import Architecture, BinaryView, SegmentFlag, log_error, FileMetadata

is_enabled = False

class LiveView(BinaryView):
    """ A custom binary view that allows arbitrary data to be written to it, without requiring that any segments
    created must exist in the actual file. This can be used to display the stack contents within Binary Ninja itself
    in the following way:
    1. After opening the binary, switch from "ELF" to "Live view"
    2. In the tools menu, click "Attach Live View"
    3. Return to the ELF view and execute the binary.
    4. Once the instruction pointer moves into the stack, the contents of the stack will be copied into the Live View
        a. Contrary to the "Live" in the title, this only happens once
    5. A function is created in the Live view wherever the instruction pointer happens to be. Switch to the Live View
        again and you should be able to see Binary Ninja's attempt at disassembling the stack as code.
    Since the disassembled stack lives in a different Binary View than the one on which Voltron's sync callback is evoked,
    it has no way of highlighting the instructions in the Live View, which severly limits the usefulness of having it.
    In light of this limitation and the convoluted process required to set up the Live View, this code has been disabled
     until Binary Ninja gets better support for appending contents to an arbitrary address in a binary. However, if you
     want to use it, flipping the 'is_enabled' boolean at the top should do the trick."""
    name = "Live View"
    long_name = "Live View"

    def __init__(self, data):
        # Binary Ninja apparently looks at the file metadata for the parent view, so we have to bind that to a Binary View as well
        self.file = FileMetadata(filename="/dev/null")
        BinaryView.__init__(self, file_metadata=self.file, parent_view=BinaryView(file_metadata=self.file), handle=None)
        self.raw = data

    @classmethod
    def is_valid_for_data(self, _data):
        return True

    def init(self):
        if is_enabled:
            try:
                self.platform = Architecture['x86'].standalone_platform
            except:
                log_error(traceback.format_exc())
                return False
        return True

    def perform_write(self, starting_address, data):
        """ Creates a new segment and section at the offset specified, just big enough to hold the data available.
        Only designed to be called once (for now)"""
        length = len(data)
        self.add_auto_segment(
            starting_address, length, 0x0, length,
            SegmentFlag.SegmentReadable | SegmentFlag.SegmentWritable,
        )
        self.add_auto_section('in_memory', starting_address, length)

        return self.write(starting_address, data)

if is_enabled:
    LiveView.register()
