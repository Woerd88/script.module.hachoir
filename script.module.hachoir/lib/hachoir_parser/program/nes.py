"""
NES file parser

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class NESHeader(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 16*8

    mirror_types = {
        0: "horizontal",
        1: "vertical",
    }

    def createFields(self):
        yield String(self, "static", 4, "NES<EOF>")
        yield UInt8(self, "PRG_ROM", "Size of PRG ROM in 16 KB units")
        yield UInt8(self, "CHR_ROM", "Size of CHR ROM in 8 KB units (Value 0 means the board uses CHR RAM)")
        #byte 6 contains flags
        yield Enum(Bit(self, "mirrorring", "0 = horizontal, 1 = vertical"), self.mirror_types)
        yield Bits(self, "battery", 1, "SRAM at 6000-7FFFh battery backed. 0= no, 1 = yes")
        yield Bits(self, "trainer", 1, "512 byte trainer at 7000-71FFh. 0= no, 1 = yes")
        yield Bits(self, "four_screen_vram", 1, "Four screen mode. 0 = no, 1 = yes")
        yield Bits(self, "lo_map_nr", 4, "Lower 4 bits of the mapper number")
        #byte 7 contains flags
        yield Bits(self, "vs_unisystem", 1, "Indicaties if this is a Vs. game. 0= no, 1 = yes")
        yield Bits(self, "playchoice", 1, "Indicaties if this is a PC-10. 0= no, 1 = yes")
        yield Bits(self, "ines20", 2, "When equal to binary 10, use NES 2.0 rules; otherwise, use other rules")
        yield Bits(self, "hi_map_nr", 4, "Higher 4 bits of the mapper number")
        #remaining bytes not used
        #do we have a iNES 2.0 header? then we can parse the other bytes as wel

        if self["ines20"].value == 2:
            yield UInt8(self, "PRG_ROM", "Size of PRG RAM in 8 KB units")
            #byte 9 contains flags
            yield Bit(self, "tv_system1", "TV system (0: NTSC; 1: PAL)")
            yield Bits(self, "reserved", 7, "Reserved, set to zero")
            #byte 10 contains flags
            yield Bits(self, "tv_system2", 2, "TV system (0: NTSC; 1: PAL)")
            yield Bits(self, "unused", 2, "")
            yield Bits(self, "PRG_RAM", 1, "PRG RAM ($6000-$7FFF) (0: present; 1: not present)")
            yield Bits(self, "board_conflicts", 1, "0: Board has no bus conflicts; 1: Board has bus conflicts")
            yield Bits(self, "unused", 2, "")
            yield NullBytes(self, "unused", 5, "Bytes not used, should be 0x00")
        else:
            yield NullBytes(self, "unused", 8, "Bytes not used, should be 0x00")

class UNIFHeader(FieldSet):
    endian = LITTLE_ENDIAN

    def createFields(self):
        yield String(self, "static", 4, "UNIF")
        yield UInt32(self, "version", "Minimum version number required to parse all chunks in file ")
        yield NullBytes(self, "unused", 24, "Bytes not used, should be 0x00")

class UNIFBlock(FieldSet):
    endian = LITTLE_ENDIAN

    def createFields(self):
        yield String(self, "type", 4, "name of type")
        yield UInt32(self, "length", "")
        yield RawBytes(self, "data", self["length"].value, "actual data")

class NESFile(Parser):
    PARSER_TAGS = {
        "id": "nes",
        "category": "program",
        "file_ext": ("nes",),
        "min_size": 16 * 8,     #TODO determin minimum size
        "description": "Nintendo Entertainment System",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        #TODO do a validation check
        if (self.stream.readBytes(0, 4) == b"NES\x1a" or self.stream.readBytes(0, 4) == "UNIF" ):
            return True
        else:
            return False

    def createFields(self):

        #parse the header
        header_type = self.stream.readBytes(0, 4)
        if (header_type == b"NES\x1a"):

            #Parse NES Header
            yield NESHeader(self, "nes_header")

        elif (header_type == "UNIF"):

            #Parse Unif Header
            yield UNIFHeader(self, "unif_header")

            #now parse all blocks of data that may come
            data = self.stream.readBytes( (self.current_size) + (4 * 8), 4)
            blocksize = struct.unpack('<I', data)[0]

            while (blocksize > 0):
                #Parse Block
                yield UNIFBlock(self, "unif_block[]")

                #is there more data?
                if self.current_size + 4 < self.size:
                    data = self.stream.readBytes( (self.current_size) + (4 * 8), 4)
                    blocksize = struct.unpack('<I', data)[0]
                else:
                    break

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")
