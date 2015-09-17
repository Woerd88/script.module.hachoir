"""
CDI 9660 (cdrom) file system parser.

Author: Ronald Schippers    (Woerd88)
Creation: 24 may 2015

Contributions:

Known Issues:


"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt16BE, UInt32, UInt32BE, Enum,
    NullBytes, RawBytes, String)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class PrimaryVolumeDescriptor(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 2041*8
    def createFields(self):
        yield NullBytes(self, "unused[]", 1)
        yield String(self, "system_id", 32, "System identifier", strip=" ")
        yield String(self, "volume_id", 32, "Volume identifier", strip=" ")
        yield NullBytes(self, "unused[]", 8)

        # doc below, iso9660 uses both endian

        yield UInt32(self, "space_size_l", "Volume space size Type L")
        yield UInt32BE(self, "space_size_m", "Volume space size Type M")
        yield NullBytes(self, "unused[]", 32)
        yield UInt16(self, "set_size_l", "Volume set size Type L")
        yield UInt16BE(self, "set_size_m", "Volume set size Type M")
        yield UInt16(self, "seq_num_l", "Volume Sequence number Type L")
        yield UInt16BE(self, "seq_num_m", "Volume Sequence number Type L")
        yield UInt16(self, "block_size_l", "Block size Type L")
        yield UInt16BE(self, "block_size_m", "Block size Type M")

        # Temp documentation: https://casper.berkeley.edu/svn/trunk/roach/sw/uboot/disk/part_iso.h

        yield UInt32(self, "path_table_size_l", "Path table size Type L")
        yield UInt32BE(self, "path_table_size_m", "Path table size Type M")
        yield UInt32(self, "occu_lpath", "Location of Occurrence of Type L Path Table")
        yield UInt32(self, "opt_lpath", "Location of Optional of Type L Path Table")
        yield UInt32BE(self, "occu_mpath", "Location of Occurrence of Type M Path Table")
        yield UInt32BE(self, "opt_mpath", "Location of Optional of Type M Path Table")

        yield RawBytes(self, "root_directory", 34)

        yield String(self, "vol_set_id", 128, "Volume set identifier", strip=" ")
        yield String(self, "publisher", 128, "Publisher identifier", strip=" ")
        yield String(self, "data_preparer", 128, "Data preparer identifier", strip=" ")
        yield String(self, "application", 128, "Application identifier", strip=" ")
        yield String(self, "copyright", 37, "Copyright file identifier", strip=" ")
        yield String(self, "abstract", 37, "Abstract file identifier", strip=" ")
        yield String(self, "biographic", 37, "Biographic file identifier", strip=" ")
        yield String(self, "creation_ts", 17, "Creation date and time", strip=" \0")
        yield String(self, "modification_ts", 17, "Modification date and time", strip=" \0")
        yield String(self, "expiration_ts", 17, "Expiration date and time", strip=" \0")
        yield String(self, "effective_ts", 17, "Effective date and time", strip=" \0")
        yield UInt8(self, "struct_ver", "Structure version")
        yield NullBytes(self, "unused[]", 1)
        yield String(self, "app_use", 512, "Application use", strip=" \0")
        yield NullBytes(self, "unused[]", 653)

class BootRecord(FieldSet):
    static_size = 2041*8
    def createFields(self):
        yield String(self, "sys_id", 31, "Boot system identifier", strip="\0")
        yield String(self, "boot_id", 31, "Boot identifier", strip="\0")
        yield RawBytes(self, "system_use", 1979, "Boot system use")

class Terminator(FieldSet):
    static_size = 2041*8
    def createFields(self):
        yield NullBytes(self, "null", 2041)

class FileSector(FieldSet):
    endian = LITTLE_ENDIAN
    def createFields(self):

        #ISO Mode 0,1,2 has a sector header
        if self.root.sector_mode > -1:
            yield SectorHeader(self, "sector_header")

        yield SectorData(self, "sector_data")

        #ISO Mode 1,2 has a sector ending
        if self.root.sector_mode > 0:
            yield SectorEnding(self, "sector_ending")

class SectorHeader(FieldSet):
    endian = LITTLE_ENDIAN
    def createFields(self):

        if self.root.sector_mode == 0:
           yield RawBytes(self, "sync", 12, "CD-ROM Mode 0: sync pattern")
           yield RawBytes(self, "address", 3, "CD-ROM Mode 0: address")
           yield UInt8(self, "mode", "CD-ROM Mode 0: mode")
        elif self.root.sector_mode == 1:
           yield RawBytes(self, "sync", 12, "CD-ROM Mode 1: sync pattern")
           yield RawBytes(self, "address", 3, "CD-ROM Mode 1: address")
           yield UInt8(self, "mode", "CD-ROM Mode 1: mode")
        elif self.root.sector_mode == 2:
           yield RawBytes(self, "sync", 12, "CD-ROM Mode 2: sync pattern")
           yield RawBytes(self, "address", 3, "CD-ROM Mode 2: address")
           yield UInt8(self, "mode", "CD-ROM Mode 2: mode")
           if self.root.sector_form == 1 or self.root.sector_form == 2:
              yield RawBytes(self, "subheader", 8, "CD-ROM XA Mode 2: subheader")

class SectorEnding(FieldSet):
    endian = LITTLE_ENDIAN
    def createFields(self):

        if self.root.sector_mode == 1:
           yield RawBytes(self, "err_detect", 4, "CD-ROM Mode 1: EDC (Error detection)")
           yield RawBytes(self, "reserved", 8, "CD-ROM Mode 1: Intermediate (reserved)")
           yield RawBytes(self, "err_p_parity", 172, "CD-ROM Mode 1: P-Parity (Error correction)")
           yield RawBytes(self, "err_q_parity", 104, "CD-ROM Mode 1: Q-Parity (Error correction)")
        elif self.root.sector_mode == 2:
            if self.root.sector_form == 1:
                yield RawBytes(self, "err_detect", 4, "CD-ROM XA Mode 2 Form 1:  (Error detection)")
                yield RawBytes(self, "err_p_parity", 172, "CD-ROM XA Mode 2 Form 1: P-Parity (Error correction)")
                yield RawBytes(self, "err_q_parity", 104, "CD-ROM XA Mode 2 Form 1: Q-Parity (Error correction)")
            elif self.root.sector_form == 2:
                yield RawBytes(self, "err_detect", 4, "CD-ROM XA Mode 2 Form 2:  (Error detection)")

class Volume(FieldSet):
    endian = BIG_ENDIAN
    TERMINATOR = 255
    type_name = {
        0: "Boot Record",
        1: "Primary Volume Descriptor",
        2: "Supplementary Volume Descriptor",
        3: "Volume Partition Descriptor",
        TERMINATOR: "Volume Descriptor Set Terminator",
    }
    static_size = 2048 * 8
    content_handler = {
        0: BootRecord,
        1: PrimaryVolumeDescriptor,
        TERMINATOR: Terminator,
    }

    def createFields(self):

        yield Enum(UInt8(self, "type", "Volume descriptor type"), self.type_name)
        yield RawBytes(self, "signature", 5, "CD-Isignature")
        yield UInt8(self, "version", "Volume descriptor version")
        cls = self.content_handler.get(self["type"].value, None)
        if cls:
            yield cls(self, "content")
        else:
            yield RawBytes(self, "raw_content", 2048-7)


class CDI(Parser):
    sector_mode = -1
    sector_form = -1

    endian = LITTLE_ENDIAN
    MAGIC = "\x01CD-I"

    NULL_BYTES = 0x8000         #16 * 2048 bytes
    PARSER_TAGS = {
        "id": "cdi",
        "category": "file_system",
        "description": "Phillips CD-I file system",
        "min_size": (NULL_BYTES + 6)*8,
        "magic": ((MAGIC, NULL_BYTES*8),),
    }

    def validate(self):

        #first 16 sectors are system area, after that the "\x01CD-I" should be there

        #first check if its a iso with sector size 2048 (0x800)
        #(ISO9660/DVD/2048) (ISO DISC IMAGE, only sectors data)
        if self.stream.readBytes(16 * 2048 * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        #Second check if its a iso with sector size 2352 (0x930) + sector header of 16 bytes
        #ISO9660/MODE0 or MODE1 or MODE2/2352 (CD SECTORS)
        if self.stream.readBytes( ((16 * 2352) + 16) * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        #Third check if its a iso with sector size 2352 (0x930) + sector header of 24 bytes
        #ISO9660/MODE2/FORM1/2352 (CD SECTORS) (XA Extension)
        if self.stream.readBytes( ((16 * 2352) + 24) * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        return False

    def createFields(self):

        #Step 1: Determin the CD ROM specifications
        #The first 16 sectors are system area, but we don't know what sector size is being used
        # let's check sector size 2046 (16 sectors x 2046 bytes per sector = 0x8000)
        if self.stream.readBytes(16 * 2048 * 8, len(self.MAGIC)) == self.MAGIC:
            #(ISO9660/DVD/2048) (ISO DISC IMAGE, only sectors data)
            self.sector_mode = -1
            self.sector_form = -1
            sector_size = 2048
            sector_header_size = 0

        # let's check sector size 2532 (16 sectors x 2532 bytes per sector = 0x9300)
        # and add the sectorheader of 16 bytes
        elif self.stream.readBytes( ((16 * 2352) + 16) * 8, len(self.MAGIC)) == self.MAGIC:
            #ISO9660/MODE0/2352 (CD SECTORS) or
            #ISO9660/MODE1/2352 (CD SECTORS) or
            #ISO9660/MODE2/2352 (CD SECTORS) Without XA Extension
            self.sector_mode = self.stream.readBytes( ((16 * 2352) + 15) * 8 , 1)
            self.sector_mode = ord(self.sector_mode)
            self.sector_form = -1
            sector_size = 2352
            sector_header_size = 16

        # let's check sector size 2532 (16 sectors x 2532 bytes per sector = 0x9300)
        # and add the sectorheader of 24 bytes
        elif self.stream.readBytes( ((16 * 2352) + 24) * 8, len(self.MAGIC)) == self.MAGIC:
            #ISO9660/MODE2/FORM1/2352 (CD SECTORS) XA Extension detected
            self.sector_mode = 2
            self.sector_form = 1
            sector_size = 2352
            sector_header_size = 24

        #Step 2: Skip this system area, not part of the ISO9660 specifications
        yield self.seekByte( (16 * sector_size), null=True)

        #Step 3: list all volumes untill the terminator shows up
        while True:

            #ISO Mode 0,1,2 has a sector header
            if self.sector_mode > -1:
                yield SectorHeader(self, "sector_header")

            #2048 Bytes user data
            volume = Volume(self, "volume[]")
            yield volume

            #ISO Mode 1,2 has a sector ending
            if self.sector_mode > 0:
                yield SectorEnding(self, "sector_ending")

            if volume["type"].value == Volume.TERMINATOR:
                break


        #We are not interested in parse the file sectors, this will only cost performance
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

