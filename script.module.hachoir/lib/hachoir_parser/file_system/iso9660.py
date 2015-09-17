"""
ISO 9660 (cdrom) file system parser.

Documents:
- Standard ECMA-119 (december 1987)
  http://www.nondot.org/sabre/os/files/FileSystems/iso9660.pdf
  http://www.ecma-international.org/publications/files/ECMA-ST/Ecma-119.pdf
- Standard ECMA-130 (june 1996)
  http://www.ecma-international.org/publications/files/ECMA-ST/Ecma-130.pdf

Author: Victor Stinner
Creation: 11 july 2006

Contributions:
24 april 2013   Garrett Brown       (Garbear)   - Added BigEndian type support + Pathtable
15 may   2015   Ronald Schippers    (Woerd88)   - Added Directory Record + Additional Pathtables + ISO modes

Known Issues:
- ISO9660/MODE2/FORM2/2352  XA Extension is never detected and will be handled as FORM1
- In the whole parse the 'Extended Attribute' isn't dealt with, but i never came across one

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
        yield DirectoryRecord(self, "root_directory")
        yield String(self, "vol_set_id", 128, "Volume set identifier", strip=" ")
        yield String(self, "publisher", 128, "Publisher identifier", strip=" ")
        yield String(self, "data_preparer", 128, "Data preparer identifier", strip=" ")
        yield String(self, "application", 128, "Application identifier", strip=" ")
        yield String(self, "copyright", 37, "Copyright file identifier", strip=" ")
        yield String(self, "abstract", 37, "Abstract file identifier", strip=" ")
        yield String(self, "biographic", 37, "Biographic file identifier", strip=" ")
        yield String(self, "creation_ts", 17, "Creation date and time", strip=" ")
        yield String(self, "modification_ts", 17, "Modification date and time", strip=" ")
        yield String(self, "expiration_ts", 17, "Expiration date and time", strip=" ")
        yield String(self, "effective_ts", 17, "Effective date and time", strip=" ")
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

class SectorData(FieldSet):
    endian = LITTLE_ENDIAN
    def createFields(self):

        if self.root.sector_mode == 0:
           yield RawBytes(self, "data", 2336, "CD-ROM Mode 0: Data")
        elif self.root.sector_mode == 1:
            yield RawBytes(self, "data", 2048, "CD-ROM Mode 1: Data")
        elif self.root.sector_mode == 2:
            if self.root.sector_form == -1:
                yield RawBytes(self, "data", 2336, "CD-ROM Mode 2: Data")
            elif self.root.sector_form == 1:
                yield RawBytes(self, "data", 2048, "CD-ROM XA Mode 2 Form 1: Data")
            elif self.root.sector_form == 2:
                yield RawBytes(self, "data", 2324, "CD-ROM XA Mode 2 Form 2: Data")

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
        yield RawBytes(self, "signature", 5, "ISO 9960 signature (CD001)")

        #if self["signature"].value != "CD001":
        #    raise ParserError("Invalid ISO 9960 volume signature")

        yield UInt8(self, "version", "Volume descriptor version")
        cls = self.content_handler.get(self["type"].value, None)
        if cls:
            yield cls(self, "content")
        else:
            yield RawBytes(self, "raw_content", 2048-7)


class DirectoryRecord(FieldSet):
    endian = LITTLE_ENDIAN
    file_flags = {
        0: "Normal File",
        1: "Hidden File",
        2: "Directory",
    }

    def createFields(self):

        #read the lenght of the directory and make it integer
        file_total_length = self.stream.readBytes(self.absolute_address, 1)
        file_total_length = ord(file_total_length)

        if (file_total_length >= 32):
            yield UInt8(self, "length", "Length of Directory Identifier")
            yield UInt8(self, "attr_length", "Extended Attribute Record Length")
            yield UInt32(self, "extent_lpath", "Location of extent (LBA) Type L")
            yield UInt32BE(self, "extent_mpath", "Location of extent (LBA) Type M")
            yield UInt32(self, "extent_size_l", "Size of extent (LBA) Type L")
            yield UInt32BE(self, "extent_size_m", "Size of extent (LBA) Type M")
            yield RawBytes(self, "recording_datetime", 7, "Recording date and time")
            yield Enum(UInt8(self, "file_flag", "File flags"), self.file_flags)
            yield UInt8(self, "file_unit_size", "File unit size for files recorded in interleaved mode, zero otherwise")
            yield UInt8(self, "interleave_gap_size", "Interleave gap size for files recorded in interleaved mode, zero otherwise")
            yield UInt16(self, "volume_seq_number_l", "Volume sequence number, the volume that this extent is recorded on Type L")
            yield UInt16BE(self, "volume_seq_number_m", "Volume sequence number, the volume that this extent is recorded on Type M")
            yield UInt8(self, "file_identifier_length", "Length of file identifier (file name)")
            file_identifier_length = self["file_identifier_length"].value
            yield RawBytes(self, "file_identifier", file_identifier_length, "file name")

            #check if the padding byte is there
            if file_identifier_length % 2 == 0:
                yield UInt8(self, "padding_byte", "Padding byte: if file_identifier_length is even this is set to 0")
                file_padding_byte = 1
            else:
                file_padding_byte = 0

            #check if there are any unused bytes
            if file_total_length - 33 - file_identifier_length - file_padding_byte > 0:
                yield RawBytes(self, "unused[]", file_total_length - 33 - file_identifier_length - file_padding_byte, "unspecified field for system use; must contain an even number of bytes")

class PathTable(FieldSet):
    endian = LITTLE_ENDIAN
    def createFields(self):
        #Are we filling up the Little Endian or Big Endian PathTable?
        islsb = self.name.startswith("path_l")
        UInt16_ = UInt16 if islsb else UInt16BE
        UInt32_ = UInt32 if islsb else UInt32BE
        yield UInt8(self, "length", "Length of Directory Identifier")
        yield UInt8(self, "attr_length", "Extended Attribute Record Length")
        yield UInt32_(self, "location", "Location of Extent where the directory is recorded (LBA)")
        yield UInt16_(self, "parent_dir", "Parent Directory Number in the path table")
        yield String(self, "name", self["length"].value, "Directory Identifier (name)", strip=" ")
        if self["length"].value % 2:
            yield NullBytes(self, "unused[]", 1)

class ISO9660(Parser):
    sector_mode = -1
    sector_form = -1
    parse_file_sectors = False  #Only set to 'True' when you have the time and CPU to parse a whole iso file

    endian = LITTLE_ENDIAN
    MAGIC = "\x01CD001"

    NULL_BYTES = 0x8000         #16 * 2048 bytes
    PARSER_TAGS = {
        "id": "iso9660",
        "category": "file_system",
        "description": "ISO 9660 file system",
        "min_size": (NULL_BYTES + 6)*8,
        "magic": ((MAGIC, NULL_BYTES*8),),
    }

    def validate(self):

        #first 16 sectors are system area, after that the "\x01CD001" should be there

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

        return "Invalid signature"

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

        pathtable_l_offset = 0
        pathtable_l_size = 0

        pathtable_m_offset = 0
        pathtable_m_size = 0

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

            if volume["type"].value == 1: # PrimaryVolumeDescriptor

                #Step 3.1: Extract Location of path table
                # Multiply LBA by sector size to get index offset
                pathtable_l_offset = volume["content/occu_lpath"].value * sector_size
                pathtable_l_size = volume["content/path_table_size_l"].value
                pathtable_m_offset = volume["content/occu_mpath"].value * sector_size
                pathtable_m_size = volume["content/path_table_size_m"].value

                # Read the optional ocurrences as well
                pathtable_opt_l_offset = volume["content/opt_lpath"].value * sector_size
                pathtable_opt_m_offset = volume["content/opt_mpath"].value * sector_size

            elif volume["type"].value == Volume.TERMINATOR:
                break

        #Step 4: List all posible pathtables from the pathtable locations thas was extracted from the PrimaryVolumeDescriptor
        for i in range(0, 4):
            if i == 0:
                pathtable_offset = pathtable_l_offset       #Little Endian (Manditory)
                pathtable_size = pathtable_l_size
                objectname = "path_l[]"
            elif i == 1:
                pathtable_offset = pathtable_opt_l_offset   #Little Endian (Optional)
                pathtable_size = pathtable_l_size
                objectname = "path_l_opt[]"
            elif i == 2:
                pathtable_offset = pathtable_m_offset       #Big Endian (Manditory)
                pathtable_size = pathtable_m_size
                objectname = "path_m[]"
            elif i == 3:
                pathtable_offset = pathtable_opt_m_offset   #Big Endian (Optional)
                pathtable_size = pathtable_m_size
                objectname = "path_m_opt[]"

            if pathtable_offset:

                #Most of the time this table is located right after the volumes
                #in this case don't add it as a field, because it will be null, and this caused the framework to end this parser
                if (pathtable_offset * 8) > self.current_size:
                    yield self.seekByte(pathtable_offset, relative=False, null=True)

                #ISO Mode 0,1,2 has a sector header
                if self.sector_mode > -1:
                    yield SectorHeader(self, "sector_header")

                while True:
                    pathtable = PathTable(self, objectname)
                    yield pathtable
                    #divide address and size by 8 since its stored in amount of bits
                    currentpath = (pathtable.absolute_address >> 3) + (pathtable.size >> 3)
                    if currentpath >= pathtable_offset + pathtable_size + sector_header_size:
                        break

                #seek to the end of the sextor so we can mark the sector ending properly
                yield self.seekByte(pathtable_offset + sector_header_size + 2048, relative=False, null=True)

                #ISO Mode 1,2 has a sector ending
                if self.sector_mode > 0:
                    yield SectorEnding(self, "sector_ending")


        #Step 5: List all directory records by looping over the path table
        #Al sectors in between are considered to be data sectors
        for i in range(0, self._field_array_count["path_l"] + 1):
            objectname = "path_l[%d]" % i
            pathtable_entry = self[objectname]
            if pathtable_entry["location"].value * sector_size * 8 >= self.current_size:

                directory_offset = pathtable_entry["location"].value * sector_size
                directory_size = 0
                directory_sector_total = 0
                directory_sector_curr = 0

                #Are we jumping to a sector? The Data in between is probably file data
                if self.parse_file_sectors == True:
                    #Be aware: Sectors size is about 2 kB, so there could be a lot of sectors for 1 file
                    while (directory_offset * 8) > self.current_size:
                        yield FileSector(self, "file_sector[]")
                else:
                    #We are not interested in parse the file sectors, this will only cost performance
                    if (directory_offset * 8) > self.current_size:
                        yield self.seekByte(directory_offset, relative=False, null=True)

                #Loop over sectors till the amount of sectors is reached
                while (directory_sector_total == 0 or  directory_sector_curr < directory_sector_total ):

                    #Increase the current sector counter
                    directory_sector_curr += 1

                    #ISO Mode 0,1,2 has a sector header
                    if self.sector_mode > -1:
                        yield SectorHeader(self, "sector_header")

                    #Loop over the directory records
                    while True:

                        #check if there is a directory record
                        directory_record_length = self.stream.readBytes(self.current_size, 1)
                        directory_record_length = ord(directory_record_length)

                        if directory_record_length > 0:
                            directory = DirectoryRecord(self, "directory_records[]")
                            yield directory

                            #if the directory extant size is not known yet, get it from first record
                            if directory_sector_total == 0:
                                directory_size = directory["extent_size_l"].value
                                directory_sector_total = directory_size / 2048
                        else:
                            break;

                    #skoop over to the end of the sector
                    directory_offset = directory_offset + sector_header_size + 2048
                    yield self.seekByte(directory_offset, relative=False)

                    #ISO Mode 1,2 has a sector ending
                    if self.sector_mode > 0:
                        yield SectorEnding(self, "sector_ending")

                    #update the directory_offset so it will always point to the start of sector
                    #is needed when there are sector ends
                    directory_offset = self.current_size / 8

        #Last Step: Did we leave anything unparsed? ... well mark it as end
        if self.parse_file_sectors == True:
            #Be aware: Sectors size is about 2 kB, so there could be a lot of sectors for 1 file
            while (self.current_size < self._size):
                yield FileSector(self, "file_sector[]")
        else:
            #We are not interested in parse the file sectors, this will only cost performance
            if self.current_size < self._size:
                yield self.seekBit(self._size, "end")

