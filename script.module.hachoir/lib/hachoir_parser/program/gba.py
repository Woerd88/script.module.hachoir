"""
Gameboy Advance file parser

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 32*8

    def createFields(self):

        #0x00 - 0x03 	32 bit ARM B Jump to start of ROM executable
        #0x04 - 0x9F 	Nintendo Logo data
        #0xA0 - 0xAB 	Game Title
        #0xAC - 0xAF 	Game Code
        #0xB0 - 0xB1 	Maker Code
        #0xB2 - 0xB2 	0x96 Fixed
        #0xB3 - 0xB3 	Main Unit Code
        #0xB4 - 0xB4 	Device Type
        #0xB5 - 0xBB 	Reserved Area
        #0xBC - 0xBC 	Mask ROM Version
        #0xBD - 0xBD 	Compliment Check
        #0xBE - 0xBF 	Reserved Area

        yield String(self, "game_title", 12, "Title of the game", strip="\0")
        yield String(self, "game_code", 4, "upper case ascii", strip="\0")
        yield String(self, "maker_code", 2, "publisher code", strip="\0")
        yield UInt8(self, "fixed", "0x96 Fixed")
        yield UInt8(self, "main_unit_code", "")
        yield UInt8(self, "device_type", "")
        yield RawBytes(self, "reserved", 7, "")
        yield UInt8(self, "version", "")
        yield UInt8(self, "checksum_compliment", "")
        yield RawBytes(self, "reserved", 2, "")

class GBAFile(Parser):
    PARSER_TAGS = {
        "id": "gba",
        "category": "program",
        "file_ext": ("gba",),
        "min_size": 192 * 8,
        "description": "Nintendo Gameboy Advance",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        nintendo_logo =    ( "\x24\xFF\xAE\x51\x69\x9A\xA2\x21\x3D\x84\x82\x0A"
                            "\x84\xE4\x09\xAD\x11\x24\x8B\x98\xC0\x81\x7F\x21\xA3\x52\xBE\x19"
                            "\x93\x09\xCE\x20\x10\x46\x4A\x4A\xF8\x27\x31\xEC\x58\xC7\xE8\x33"
                            "\x82\xE3\xCE\xBF\x85\xF4\xDF\x94\xCE\x4B\x09\xC1\x94\x56\x8A\xC0"
                            "\x13\x72\xA7\xFC\x9F\x84\x4D\x73\xA3\xCA\x9A\x61\x58\x97\xA3\x27"
                            "\xFC\x03\x98\x76\x23\x1D\xC7\x61\x03\x04\xAE\x56\xBF\x38\x84\x00"
                            "\x40\xA7\x0E\xFD\xFF\x52\xFE\x03\x6F\x95\x30\xF1\x97\xFB\xC0\x85"
                            "\x60\xD6\x80\x25\xA9\x63\xBE\x03\x01\x4E\x38\xE2\xF9\xA2\x34\xFF"
                            "\xBB\x3E\x03\x44\x78\x00\x90\xCB\x88\x11\x3A\x94\x65\xC0\x7C\x63"
                            "\x87\xF0\x3C\xAF\xD6\x25\xE4\x8B\x38\x0A\xAC\x72\x21\xD4\xF8\x07" )
        #Check if the logo is there
        if (self.stream.readBytes(0x04 * 8, len(nintendo_logo)) == nintendo_logo ):
            return True
        else:
            return False

    def createFields(self):

        yield self.seekByte(0x04)
        yield RawBytes(self, "nintendo_logo", 156, "static boot logo")

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

