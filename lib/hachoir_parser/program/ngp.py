"""
Neo Geo Pocket file parser

Documents
- Neo Pop source

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 64*8

    def createFields(self):

        yield String(self, "license", 28, "", strip=" ")
        yield UInt32(self, "start_pc", "")
        yield UInt16(self, "catalog", "")
        yield UInt8(self, "sub_catalog", "")
        yield UInt8(self, "mode", "")
        yield String(self, "game_title", 12, "")
        yield RawBytes(self, "reserved", 16, "")

class NeoGeoPocketFile(Parser):
    PARSER_TAGS = {
        "id": "ngp",
        "category": "program",
        "file_ext": ("ngp",),
        "min_size": 64 * 8,
        "description": "Neo Geo Pocket",
    }
    endian = LITTLE_ENDIAN

    def validate(self):

        #Only allow roms upto 32 Mbit
        if (self.size > 32 * 1024 * 1024):
            return False

        null_bytes_reserved =    ( "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" )
        #Check if the reserved bytes are there
        if (self.stream.readBytes(0x30 * 8, len(null_bytes_reserved)) == null_bytes_reserved ):
            return True
        else:
            return False

    def createFields(self):

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

