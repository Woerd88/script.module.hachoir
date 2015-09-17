"""
PC-FX CD-ROM file system parser.

Documents:
https://github.com/jbrandwood/pcfxtools/blob/master/pcfx-cdlink.c

Author: Ronald Schippers       (Woerd88)
Creation: 25 may 2015

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt16BE, UInt32, UInt32BE, Enum,
    NullBytes, RawBytes, String)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    #static_size = 2041*8
    def createFields(self):
        yield String(self, "magic", 16, "should be PC-FX:Hu_CD-ROM ")
        yield RawBytes(self, "unk", 2032, "")
        yield String(self, "title", 20, "")
        yield UInt32(self, "sector_off", "")
        yield UInt32(self, "sector_count", "")
        yield UInt32(self, "prog_off", "")
        yield UInt32(self, "prog_point", "")
        yield String(self, "maker_id", 4, "")
        yield String(self, "maker_name", 60, "")
        yield UInt32(self, "volume_no", "")
        yield UInt16(self, "version", "")
        yield UInt16(self, "country", "")
        yield String(self, "date", 8, "")
        yield RawBytes(self, "padding", 896, "")
        yield RawBytes(self, "udata", 1024, "")


class PCFXFile(Parser):
    endian = LITTLE_ENDIAN
    MAGIC = "PC-FX:Hu_CD-ROM "

    PARSER_TAGS = {
        "id": "pcfx",
        "category": "program",
        "description": "PC-FX",
        "min_size": (1024)*8,
    }

    def validate(self):

        if self.stream.readBytes(0x95A7F0 * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        return False

    def createFields(self):

        #skip first part
        yield self.seekByte( 0x95A7F0 , null=True)

        yield Header(self, "header")

        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

