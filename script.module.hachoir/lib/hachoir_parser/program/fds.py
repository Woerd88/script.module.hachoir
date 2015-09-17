"""
Nintendo Family Computer Disk System file parser

Documents:
- http://wiki.nesdev.com/w/index.php/Family_Computer_Disk_System#.FDS_format

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 56*8

    def createFields(self):

        yield UInt8(self, "block_code", "should be 0x01")
        yield String(self, "magic", 14, "should be *NINTENDO-HVC*")
        yield UInt8(self, "maker_code", "")
        yield String(self, "game_title", 3, " 3 letter game name")
        yield UInt8(self, "game_type", "")
        yield UInt8(self, "game_version", "")
        yield UInt8(self, "side_nr", "$00 = Side A, $01 = Side B. Single-sided disks use $00 ")
        yield UInt8(self, "disc_nr", "")
        yield UInt8(self, "disc_type", "$00 = FMC (normal card), $01 = FSC (card with shutter)")
        yield UInt8(self, "unknown", "")
        yield UInt8(self, "boot_code", "Refers to the file code/file number to load upon boot/start-up ")
        yield RawBytes(self, "unknown", 5, " all 0xFF")
        yield RawBytes(self, "date", 3, "")
        yield UInt8(self, "country", "0x49 = Japan")
        yield UInt8(self, "unknown", "Region?")
        yield UInt8(self, "unknown", "Location/Site?")
        yield RawBytes(self, "unknown", 2, "0x00 and 0x02")
        yield RawBytes(self, "unknown", 5, "")
        yield RawBytes(self, "rewritten_date", 3, "")
        yield UInt8(self, "unknown", "")
        yield UInt8(self, "unknown", "0x80")
        yield RawBytes(self, "writer_serial", 2, "Disk Writer serial number")
        yield UInt8(self, "unknown", "0x07")
        yield UInt8(self, "rewrite_count", "")
        yield UInt8(self, "disc_side", "$00 = Side A, $01 = Side B ")
        yield UInt8(self, "unknown", "")
        yield UInt8(self, "price", "")
        yield UInt16(self, "crc", "")

class FDSFile(Parser):
    PARSER_TAGS = {
        "id": "fds",
        "category": "program",
        "file_ext": ("fds",),
        "min_size": 192 * 8,
        "description": "Nintendo Family Computer Disk System",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        magic =    ( "\x01*NINTENDO-HVC*")
        #Check if the logo is there
        if (self.stream.readBytes(0x00, len(magic)) == magic ):
            return True
        else:
            return False

    def createFields(self):

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

