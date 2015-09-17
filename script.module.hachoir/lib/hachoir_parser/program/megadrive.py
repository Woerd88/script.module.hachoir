"""
Sega Mega Drive / Genesis / 32x file parser

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 256*8

    def createFields(self):
        yield String(self, "console_name", 16,  "Should be either SEGA GENESIS or SEGA MEGA DRIVE")
        yield String(self, "firm_name", 16,  "Firm name and build date")
        yield String(self, "domestic_name", 48,  "")
        yield String(self, "international_name", 48,  "")
        yield String(self, "prog_type", 3,  "GM (game) or AL (educational)")
        yield String(self, "serial", 8,  "XXXXXXXX-XX", strip=" ")
        yield String(self, "version", 3,  "", strip="-")
        yield UInt16(self, "checksum", "16 bit checksum")
        yield RawBytes(self, "io_device", 16, "")
        yield UInt32(self, "rom_start", "rom start address")
        yield UInt32(self, "rom_end", "rom end address")
        yield UInt32(self, "ram_start", "ram backup start address")
        yield UInt32(self, "ram_end", "ram backup end address")
        yield String(self, "modem", 20,  "modem support")
        yield RawBytes(self, "memo", 40, "")
        yield String(self, "country_codes", 16,  "")

class SMDHeader(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 512*8

    #All files generated and accepted by the SMD have a 512-byte header.
    #The basic layout is as follows:

     #Byte 00h : Size of file.
     #Byte 01h : File data type.
     #Byte 02h : Status flags.
     #Byte 08h : Identifier 1.
     #Byte 09h : Identifier 2.
     #Byte 0Ah : File type.

     #The file data type can have the following values:
     #00h - 32K SRAM data
     #01h - Z80 program
     #02h - BIOS program, loaded at $8000
     #03h - 68000 program

     #Bit 6 of the status flags is set for a multiple file set.
     #A single file, or the last file in a set, will have bit 6 cleared.
     #The function of the remaining flags is unknown.
     #According to some SWC programming information, if the two identifier
     #bytes are set to AAh and BBh, respectively, then byte 0Ah is valid
     #and can have the following settings:
     #06h - 68000 game file
     #307h - SRAM file

    def createFields(self):
        yield UInt8(self, "size", "Size of file in 16K blocks")
        yield UInt8(self, "data_type", "")
        yield UInt8(self, "status_flags", "")
        yield RawBytes(self, "unknown", 5, "")
        yield UInt8(self, "identifier1", "0xAA")
        yield UInt8(self, "identifier2", "0xBB")
        yield UInt8(self, "file_type", "")

class MegaDriveFile(Parser):
    PARSER_TAGS = {
        "id": "megadrive",
        "category": "program",
        "file_ext": ("bin",),
        "min_size": 335 * 8,
        "description": "Sega MegaDrive / Genesis / 32X",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        magic_megadrive = "SEGA MEGA DRIVE"
        magic_genesis = "SEGA GENESIS"
        magic_32x = "SEGA 32X"

        if (self.stream.readBytes(0x100 * 8, len(magic_megadrive)) == magic_megadrive ):
            return True

        if (self.stream.readBytes(0x100 * 8, len(magic_genesis)) == magic_genesis ):
            return True

        if (self.stream.readBytes(0x100 * 8, len(magic_32x)) == magic_32x ):
            return True

        #check the Super Magic Drive copier header
        data = self.stream.readBytes(0, 11)
        if data[1] == "\x03" and data[8] == "\xAA" and data[9] == "\xBB" and data[10] == "\x06":
            return True

        return False

    def createFields(self):

        #first check if we have a SMD header
        data = self.stream.readBytes(0, 11)
        if data[1] == "\x03" and data[8] == "\xAA" and data[9] == "\xBB" and data[10] == "\x06":
            yield SMDHeader(self, "smd_header")
        else:
            #seek to the entry point 0x100
            yield self.seekByte(0x100)
            yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

