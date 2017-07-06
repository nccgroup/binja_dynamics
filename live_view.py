import struct
import traceback

from binaryninja import Architecture, BinaryView, SegmentFlag, log_error, FileMetadata

is_enabled = False

class LiveView(BinaryView):
    name = "Live View"
    long_name = "Live View"

    def __init__(self, data):
        self.file = FileMetadata(filename="/dev/null")
        BinaryView.__init__(self, file_metadata=self.file, parent_view=BinaryView(file_metadata=self.file), handle=None)
        self.raw = data

    @classmethod
    def is_valid_for_data(self, _data):
        return is_enabled

    def init(self):
        try:
            self.platform = Architecture['x86'].standalone_platform
        except:
            log_error(traceback.format_exc())
            return False
        return True

    def perform_write(self, starting_address, data):
        length = len(data)
        self.add_auto_segment(
            starting_address, length, 0x0, length,
            SegmentFlag.SegmentReadable | SegmentFlag.SegmentWritable,
        )
        self.add_auto_section('in_memory', starting_address, length)

        return self.write(starting_address, data)

LiveView.register()
