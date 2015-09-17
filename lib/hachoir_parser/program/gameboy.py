"""
Gameboy file parser

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 28*8

    def createFields(self):
        #read up front if this game is CGB (Game boy Color) support, because if so the title field will be smaller
        cbg_support = self.stream.readBytes((0x143 * 8), 1)
        if cbg_support != "\x80" and cbg_support != "\xC0":
            yield String(self, "game_title", 16, "upper case ascii")
        else:
            yield String(self, "game_title", 11, "upper case ascii", strip="\0")
            yield String(self, "manufacturer_code", 4, "upper case ascii", strip="\0")
            yield UInt8(self, "CGB_Flag", "0x80 = CBG Support, 0xC0 = CBG Only")

        yield String(self, "license_code", 2,  "Company or publisher of the game")
        yield UInt8(self, "SGB_Flag", "0x00 = No SGB Support, 0x03 = SGB support")
        yield UInt8(self, "catridge_type", "Specifies which Memory Bank Controller is used in the cartridge, ")
        yield UInt8(self, "rom_size", "Specifies the ROM Size of the cartridge")
        yield UInt8(self, "ram_size", "Specifies the ROM Size of the cartridge")
        yield UInt8(self, "destination_code", "0x00 Japanese, 0x01 Non-Japanese")
        yield UInt8(self, "license_code_old", "")
        yield UInt8(self, "rom_version", "version number of the game")
        yield UInt8(self, "checksum_headr", "")
        yield UInt16(self, "checksum_global", "")

class GameboyFile(Parser):
    PARSER_TAGS = {
        "id": "gameboy",
        "category": "program",
        "file_ext": ("gb", "gbc"),
        "min_size": 335 * 8,
        "description": "Nintendo Gameboy",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        nintendo_logo = "\xCE\xED\x66\x66\xCC\x0D\x00\x0B\x03\x73\x00\x83\x00\x0C\x00\x0D\x00\x08\x11\x1F\x88\x89\x00\x0E\xDC\xCC\x6E\xE6\xDD\xDD\xD9\x99\xBB\xBB\x67\x63\x6E\x0E\xEC\xCC\xDD\xDC\x99\x9F\xBB\xB9\x33\x3E"
        #Check if the logo is there
        if (self.stream.readBytes(0x104 * 8, len(nintendo_logo)) == nintendo_logo ):
            return True
        else:
            return False

    def createFields(self):

        #seek to the entry point 0x100
        yield self.seekByte(0x100)
        yield RawBytes(self, "entry_point", 4, "After displaying the Nintendo Logo, the built-in boot procedure jumps to this address 0x100,")
        yield RawBytes(self, "nintendo_logo", 48, "static boot logo")

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

