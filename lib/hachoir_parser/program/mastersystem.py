"""
Sega Mastersystem   file parser
Sega GameGear       file parser

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 16*8

    def createFields(self):

        yield String(self, "id", 8,  "Should be TMR SEGA")
        yield RawBytes(self, "reserved", 2, "")
        yield UInt16(self, "checksum", "16 bit checksum")
        #yield RawBytes(self, "product_code", 2, "Product codes in Binary Coded Decimal. XXXXXX")
        yield Bits(self, "product_code", 20, "Product codes in Binary Coded Decimal. XXXXXX")
        yield Bits(self, "product_version", 4, "Product version")
        yield Bits(self, "region_code", 4, "Product version")
        yield Bits(self, "rom_size", 4, "rom size")


class MasterSystemFile(Parser):
    PARSER_TAGS = {
        "id": "mastersystem",
        "category": "program",
        "file_ext": ("bin",),
        "min_size": 335 * 8,
        "description": "Sega Master System",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        #look for the header
        if GetHeaderOffset(self) > 0:
            return True
        else:
            return False

    def createFields(self):

        offset = GetHeaderOffset(self)
        yield self.seekByte(offset)

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

def GetHeaderOffset(MasterSystemFile):

    magic_mastersystem = "TMR SEGA"
    magic_homebrew = "SDSC"

    #check if we can match the rom_size with the actual size on LoROM
    if (MasterSystemFile.stream.readBytes(0x1FF0 * 8, len(magic_mastersystem)) == magic_mastersystem ):
        return 0x1FF0

    if (MasterSystemFile.stream.readBytes(0x3FF0 * 8, len(magic_mastersystem)) == magic_mastersystem ):
        return 0x3FF0

    if (MasterSystemFile.stream.readBytes(0x7FF0 * 8, len(magic_mastersystem)) == magic_mastersystem ):
        return 0x7FF0

    if (MasterSystemFile.stream.readBytes(0x81F0 * 8, len(magic_mastersystem)) == magic_mastersystem ):
        return 0x81F0

    if (MasterSystemFile.stream.readBytes(0x7FE0 * 8, len(magic_homebrew)) == magic_homebrew ):
        return 0x7FE0

    return 0

