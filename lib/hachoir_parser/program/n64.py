"""
Nintendo 64 file parser

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN, MIDDLE_ENDIAN

import struct

class Header(FieldSet):
    static_size = 32*8

    def createFields(self):

        yield String(self, "game_title", 20, "Title of the game", strip="\0")
        yield RawBytes(self, "reserved", 4, "")
        yield RawBytes(self, "publisher", 4, "")
        yield String(self, "game_code", 2, "", strip="\0")
        yield String(self, "region_code", 1, "", strip="\0")
        yield UInt8(self, "rom_version", "")

class N64File(Parser):
    PARSER_TAGS = {
        "id": "n64",
        "category": "program",
        "file_ext": ("n64",),
        "min_size": 192 * 8,
        "description": "Nintendo 64",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        #BIG_ENDIAN = "ABCD"
        #LITTLE_ENDIAN = "DCBA"
        #MIDDLE_ENDIAN = "BADC"
        #NETWORK_ENDIAN = BIG_ENDIAN

        magic1 = "\x80\x37\x12\x40" # big-endian    [ABCD] BIG_ENDIAN
        magic2 = "\x37\x80\x40\x12" # byte swapped  [BADC] MIDDLE_ENDIAN
        magic3 = "\x40\x12\x37\x80" # little-endian [DCBA] LITTLE_ENDIAN
        magic4 = "\x12\x40\x80\x37" # word swapped  [CDAB]

        #Check if the logo is there
        data = self.stream.readBytes(0, len(magic1))

        if data == magic1:
            return True

        if data == magic2:
            return True

        if data == magic2:
            return True

        if data == magic2:
            return True

        return False


    def createFields(self):

        yield self.seekByte(0x20)
        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")


def ConvertEndian(data):

    data[::4], data[1::4], data[2::4], data[3::4] = data[2::4], data[3::4], data[::4], data[1::4]
