"""
WonderSwan / Color ROM File parser

Documentation:
- http://datacrystal.romhacking.net/wiki/Template:WSx
- http://www.zophar.net/fileuploads/2/10805ixdtg/wstech23.txt

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, Bit, Bits, Enum, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

import struct

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 10*8

    def createFields(self):
        yield UInt8(self, "developer_id", "")
        yield UInt8(self, "min_system", "0x00 = WS Mono, 0x01 = WS Color")
        yield UInt8(self, "cart_id",  "")
        yield UInt8(self, "unknown",  "")
        yield UInt8(self, "rom_size",  "")
        yield UInt8(self, "sram_size",  "")
        yield UInt8(self, "capabilities",  "")
        yield UInt8(self, "rtc",  "")
        yield UInt16(self, "checksum",  "")

class WonderSwanFile(Parser):
    PARSER_TAGS = {
        "id": "wonderswan",
        "category": "program",
        "file_ext": ("ws",),
        "min_size": 1024 * 8,
        "description": "WonderSwan",
    }

    endian = LITTLE_ENDIAN

    def validate(self):

        #read all data so we can do checksum
        data = self.stream.readBytes(0, (self.size / 8 - 2))
        read_checksum = self.stream.readBytes(self.size - (2 *8) , 2)
        read_checksum = 256 * ord(read_checksum[1]) + ord(read_checksum[0])
        #calculate checksum
        calc_checksum = sum(map(ord, data))
        calc_checksum = calc_checksum & 0xFFFF

        if calc_checksum == read_checksum:
            return True
        else:
            return False

    def createFields(self):

        #seek to the end where the 'header' is located
        yield self.seekByte(self.size / 8 - 10)

        yield Header(self, "header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

wsc_system = {
    "\x00" : "WonderSwan",
    "\x01" : "WonderSwan Color",
}

wsc_rom_size = {
    "\x01" : "1Mbit?",
    "\x02" : "4Mbit",
    "\x03" : "8Mbit",
    "\x04" : "16Mbit",
    "\x05" : "24Mbit?",
    "\x06" : "32Mbit",
    "\x07" : "48Mbit?",
    "\x08" : "64Mbit",
    "\x09" : "128Mbit",
}

wsc_save_types = {
    "\x00" : "None",
    "\x01" : "64Kbit SRAM",
    "\x02" : "256Kbit SRAM",
    "\x03" : "1Mbit SRAM",
    "\x04" : "2Mbit SRAM",
    "\x10" : "1Kbit EEPROM",
    "\x20" : "16Kbit EEPROM",
    "\x50" : "8Kbit EEPROM",
}

wsc_developers = {
    "\x01": "Bandai",
    "\x02": "Taito",
    "\x03": "Tomy",
    "\x04": "Koei",
    "\x05": "Data East",
    "\x06": "Asmik Ace",
    "\x07": "Media Entertainment",
    "\x08": "Nichibutsu",
    "\x0A": "Coconuts Japan",
    "\x0B": "Sammy",
    "\x0C": "Sunsoft",
    "\x0D": "Mebius",
    "\x0E": "Banpresto",
    "\x10": "Jaleco",
    "\x11": "Imagineer",
    "\x12": "Konami",
    "\x16": "Kobunsha",
    "\x17": "Bottom Up",
    "\x18": "Naxat | Mechanic Arms? |  Media Entertainment?",
    "\x19": "Sunrise",
    "\x1A": "Cyberfront",
    "\x1B": "Megahouse",
    "\x1D": "Interbec",
    "\x1E": "NAC",
    "\x1F": "Emotion | Bandai Visual??",
    "\x20": "Athena",
    "\x21": "KID",
    "\x24": "Omega Micott",
    "\x25": "Upstar",
    "\x26": "Kadokawa/Megas",
    "\x27": "Cocktail Soft",
    "\x28": "Squaresoft",
    "\x2B": "TomCreate",
    "\x2D": "Namco",
    "\x2F": "Gust",
    "\x36": "Capcom",
}