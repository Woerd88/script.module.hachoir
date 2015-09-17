"""
SNES file parser

- Super Magicom     (*.smc)
- Super Wild Card   (*.swc)
- Pro Fighter       (*.fig)

"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, String, RawBytes, NullBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class SMCHeader(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 512*8
    def createFields(self):
        yield UInt16(self, "rom_size", "The size of the ROM dump, in units of 8 kilobytes")
        yield UInt8(self, "bin_flags", "Binary flags for the ROM layout and the save-RAM size")
        yield NullBytes(self, "reserved[]", 509)

class SWCHeader(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 512*8
    def createFields(self):
        yield UInt16(self, "rom_size", "The size of the ROM dump, in units of 8 kilobytes")
        yield UInt8(self, "bin_flags", "Binary flags for the ROM layout and the save-RAM size")
        yield NullBytes(self, "reserved[]", 5)
        yield RawBytes(self, "static", 3, "The string $aa $bb $04, with $aa at offset 8, $bb at offset 9, $04 at offset 10")
        yield NullBytes(self, "reserved[]", 501)

class FIGHeader(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 512*8
    def createFields(self):
        yield UInt16(self, "rom_size", "The size of the ROM dump, in units of 8 kilobytes")
        yield UInt8(self, "bin_flags", "$40 if this is a split file but not the last image, or $00 otherwise")
        yield UInt8(self, "hi_lo", "$80 for HiROM or $00 for LoROM")
        yield RawBytes(self, "dsp1", 2, "DSP-1 settings")
        yield NullBytes(self, "reserved[]", 506)

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 64*8
    def createFields(self):
        yield String(self, "game_title", 21, strip=" ")
        yield UInt8(self, "rom_layout", "ROM layout, typically $20 for LoROM, or $21 for HiROM. Add $10 for FastROM")
        yield UInt8(self, "cart_type", "Cartridge type, typically $00 for ROM only, or $02 for ROM with save-RAM")
        yield UInt8(self, "rom_size")
        yield UInt8(self, "ram_size")
        yield UInt8(self, "country_code")
        yield UInt8(self, "license_code")
        yield UInt8(self, "version")
        yield UInt16(self, "checksum", "Checksum complement, which is the bitwise-xor of the checksum and $ffff")
        yield UInt16(self, "snes_checksum", " SNES checksum, an unsigned 16-bit checksum of bytes")
        yield RawBytes(self, "unknown", 4)
        yield RawBytes(self, "vectors_native", 12)
        yield RawBytes(self, "unknown", 4)
        yield RawBytes(self, "vectors_emulation", 12)

class SNESFile(Parser):
    PARSER_TAGS = {
        "id": "snes",
        "category": "program",
        "file_ext": ("smc",),
        "min_size": 14 * 8,     #TODO determin minimum size
        "description": "Super Nintendo Entertainment System",
    }

    endian = LITTLE_ENDIAN

    def validate(self):
        #TODO do a validation check

        #first detect if the rom has a header with static values
        #and check the size
        header_type = GetHeaderType(self)
        if header_type == "ERR":
            return False

        #check if we have a header or not
        bank = GetBankType(self, header_type)

        if header_type == "NONE": rom_start = 0
        else: rom_start = 512

        #TODO: Add checksum check here

        #Get checksum values
        if (bank == "LoROM"):
            data = self.stream.readBytes((rom_start + 0x7FC0 + 28) * 8,  4)
        elif(bank == "HiROM"):
            data = self.stream.readBytes((rom_start + 0xFFC0 + 28) * 8,  4)
        else:
            return False

        #get checksum
        rom_compl_checksum = 256 * ord(data[1]) + ord(data[0])
        rom_snes_checksum = 256 * ord(data[3]) + ord(data[2])

        #check the complement checksum
        if rom_snes_checksum ^ 0xFFFF == rom_compl_checksum:
            return True
        else:
            return False

        ##calculate the checksum so we can determin if it's a low or high rom
        ##read the total_rom
        #total_rom = self.stream.readBytes(rom_start, self.size / 8 - rom_start)
        #calc_checksum = checksum_calc_sum(total_rom, len(total_rom))
        #calc_checksum = calc_checksum & 0xFFFF

        #if calc_checksum == rom_snes_checksum:
        #    return True
        #else:
        #    return False

        return True

    def createFields(self):

        #Check if we have a headerless rom or not
        header_type = GetHeaderType(self)
        if header_type == "SMC":
            yield SMCHeader(self, "SMC_header")
        elif header_type == "FIG":
            yield FIGHeader(self, "FIG_header")
        elif header_type == "HEADER":
            yield self.seekByte(512, relative=False)

        #store the ROM start
        if header_type == "NONE": rom_start = 0
        else: rom_start = 512

        bank = GetBankType(self, header_type)

        #jump to the snes header
        if (bank == "LoROM"):
            yield self.seekByte(rom_start + 0x7FC0, relative=False)
        elif(bank == "HiROM"):
            yield self.seekByte(rom_start + 0xFFC0, relative=False)

        #parse the header
        yield Header(self, "snes_header")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

def checksum_calc_sum(data, length):
    return sum(map(ord, data))


def checksum_mirror_sum (start, length,  mask):

	#from NSRT
	while ((length & mask) == False):
		mask >>= 1

	part1 = checksum_calc_sum(start, mask)
	part2 = 0

	next_length = length - mask;
	if (next_length):

		part2 = checksum_mirror_sum(start[:mask], next_length, mask >> 1);

		while (next_length < mask):
			next_length += next_length;
			part2 += part2;

		length = mask + mask;

	return (part1 + part2);

#in bytes and bytes
def CheckRomSize(data, actual):

    if (data == 2 * 1024 * 1024):  #2 MB   = 16MBit    -> But also 10 / 12 / 20 Mbit

        if (actual * 8) in \
            [(10 * 1024 * 1024),  (12 * 1024 * 1024), \
            (16 * 1024 * 1024), (20 * 1024 * 1024)]:
            return True
        else:
            return False

    elif (data == 4 * 1024 * 1024): #4 MB   = 32MBit    -> But also 20, 24, 48 Mbit
        if (actual * 8) in \
            [(20 * 1024 * 1024),  (24 * 1024 * 1024), \
            (32 * 1024 * 1024), (48 * 1024 * 1024)]:
            return True
        else:
            return False
    else:
        #value must be an exact match
        if (data == actual):
            return True
        else:
            return False

    return

def GetActualRomRamSize(data):

    if data == 0x00:
        return 0
    elif data == 0x01:
        return 2 * 1024         #2 kB
    elif data == 0x02:
        return 4 * 1024         #4 kB
    elif data == 0x03:
        return 8 * 1024         #8 kB
    elif data == 0x04:
        return 16 * 1024        #16 kB
    elif data == 0x05:
        return 32 * 1024        #32 kB
    elif data == 0x06:
        return 64 * 1024        #64 kB
    elif data == 0x07:
         return 128 * 1024      #128 kB
    elif data == 0x08:
        return 256 * 1024       #256 kB = 2MBit
    elif data == 0x09:
        return 512 * 1024       #512 kB = 4MBit
    elif data == 0x0A:
        return 1 * 1024 * 1024  #1 MB   = 8MBit
    elif data == 0x0B:
        return 2 * 1024 * 1024  #2 MB   = 16MBit    -> But also 10 / 12 / 20
    elif data == 0x0C:
        return 4 * 1024 * 1024  #4 MB   = 32MBit    -> But also 24, 48
    else:
        return -1



def GetBankType(SNESFile, header_type):

    if header_type == "NONE":
        rom_start = 0
    else:
        rom_start = 512

    #check if we can match the rom_size with the actual size on LoROM
    data = SNESFile.stream.readBytes((rom_start + 0x7FC0 + 23) * 8,  1)
    lo_romsize = GetActualRomRamSize(ord(data))
    if CheckRomSize(lo_romsize, (SNESFile.size / 8) - rom_start) == True:
        return "LoROM"

    #check if we can match the rom_size with the actual size on HiROM
    data = SNESFile.stream.readBytes((rom_start + 0xFFC0 + 23) * 8,  1)
    hi_romsize = GetActualRomRamSize(ord(data))
    if CheckRomSize(hi_romsize, (SNESFile.size / 8) - rom_start) == True:
        return "HiROM"

    return ""

def GetHeaderType(SNESFile):
        """
        Check for a 512-byte SMC, SWC or FIG header prepended to the beginning
        of the file.
        """

        data = SNESFile.stream.readBytes(0, 11)

        if ord(data[8]) == 0xaa and ord(data[9]) == 0xbb and ord(data[10]) == 0x04:
            # Found an SMC/SWC identifier (Source: MAME and ZSNES)
            return "SMC"
        if (ord(data[4]), ord(data[5])) in [(0x00, 0x80), (0x11, 0x02), (0x47, 0x83), (0x77, 0x83), \
                                  (0xDD, 0x02), (0xDD, 0x82), (0xF7, 0x83), (0xFD, 0x82)]:
            # Found a FIG header (Source: ZSNES)
            return "FIG"
        if ord(data[1]) << 8 | ord(data[0]) == (SNESFile.size - 512) >> 13:
            # Some headers have the rom size at the start, if this matches with
            # the actual rom size, we probably have a header (Source: MAME)
            return "HEADER"
        if SNESFile.size / 8 % 0x8000 == 512:
            # As a last check we'll see if there's exactly 512 bytes extra
            # to this image. MAME takes len modulus 0x8000 (32kb), Snes9x
            # uses len / 0x2000 (8kb) * 0x2000.
            return "HEADER"
        if SNESFile.size / 8 % 0x8000 == 0:
            # As a last check we'll see if there's exactly 512 bytes extra
            # to this image. MAME takes len modulus 0x8000 (32kb), Snes9x
            # uses len / 0x2000 (8kb) * 0x2000.
            return "NONE"

        return "ERR"
