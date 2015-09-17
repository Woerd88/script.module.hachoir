"""
Nintendo Virtual Boy ROM File parser

Documentation:
- http://www.planetvb.com/content/downloads/documents/stsvb.html

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 544*8

    def createFields(self):
        yield String(self, "game_title", 20,  "Title of the Game", strip=" ")
        yield NullBytes(self, "reserved", 5,  "")
        yield String(self, "maker_code", 2,  "")
        yield String(self, "game_code", 4,  "")
        yield UInt8(self, "version", "version")

        yield RawBytes(self, "int_gamepad",     16, "Program code of Game Pad interrupt handler")
        yield RawBytes(self, "int_timer",       16,  "Program code of Timer Zero interrupt handler")
        yield RawBytes(self, "int_cartridge",   16,  "Program code of Cartridge interrupt handler")
        yield RawBytes(self, "int_link",        16,  "Program code of Link interrupt handler")
        yield RawBytes(self, "int_vip",         16,  "Program code of VIP interrupt handler")
        yield RawBytes(self, "unused",          272,  "")
        yield RawBytes(self, "ex_float",        32,  "Program code of floating-point exception handler")
        yield RawBytes(self, "ex_zero",         16,  "Program code of zero division exception handler")
        yield RawBytes(self, "ex_opcode",       16,  "Program code of invalid opcode exception handler")
        yield RawBytes(self, "vector_lower",    16,  "Program code of handler for lower 16 TRAP vectors")
        yield RawBytes(self, "vector_upper",    16,  "Program code of handler for upper 16 TRAP vectors")
        yield RawBytes(self, "trap_handler",    16,  "Program code of address trap handler")
        yield RawBytes(self, "ex_duplexed",     32,  "Program code of duplexed exception/MNI handler")
        yield RawBytes(self, "int_rst",         16,  "Program code of reset interrupt handler")


class VirtualBoyFile(Parser):
    PARSER_TAGS = {
        "id": "virtualboy",
        "category": "program",
        "file_ext": ("vb",),
        "min_size": 1024 * 8,
        "description": "Nintendo Virtual Boy",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        null_bytes = "\x00\x00\x00\x00\x00"
        #check if the reserved bytes match

        if self.stream.readBytes(self.size - (524 * 8), len(null_bytes)) != null_bytes:
            return False

        if (self.size / 8 % 1024 != 0):
            return False

        return True

    def createFields(self):

        #seek to the end where the 'header' is located
        yield self.seekByte(self.size / 8 - 544)

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

