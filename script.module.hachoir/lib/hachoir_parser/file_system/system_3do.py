"""
3DO CD-ROM file system parser

Documents:
- http://sourcecodebrowser.com/disktype/8/cdrom_8c_source.html

Author: Ronald Schippers    (Woerd88)
Creation: 24 may 2015

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt16BE, UInt32, UInt32BE, Enum,
    NullBytes, RawBytes, String)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class System3DO(Parser):
    endian = LITTLE_ENDIAN
    PARSER_TAGS = {
        "id": "system_3do",
        "file_ext": ("bin", "iso"),
        "category": "file_system",
        "min_size": 335 * 8,
        "description": "3DO CD-ROM file system",
    }

    def validate(self):

        MAGIC1 = "\x01\x5A\x5A\x5A\x5A\x5A\x01\x00"
        MAGIC2 = "CD-ROM"

        if (self.stream.readBytes(0, len(MAGIC1)) == MAGIC1 and self.stream.readBytes(0x28 * 8, len(MAGIC2)) == MAGIC2):
            return True

        return False

    def createFields(self):

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

