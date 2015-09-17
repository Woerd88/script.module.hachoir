"""
Playstation .sfo file parser

Used by PSP and PS3

File format references:
- http://www.psdevwiki.com/ps3/PARAM.SFO
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, String, RawBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class Header(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 14*8
    def createFields(self):
        yield RawBytes(self, "magic", 4, "magic Always PSF")
        yield RawBytes(self, "version", 4, "version")
        yield UInt32(self, "keytable_start", "Start offset of keytable")
        yield UInt32(self, "datatable_start", "Start offset of datatable")
        yield UInt32(self, "tables_entries", "Number of entries in all tables")

class IndexTable(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 16*8
    def createFields(self):
        yield UInt16(self, "key_offset", "param_key offset (relative to start offset of key_table)")
        yield UInt16(self, "data_fmt", "param_data data type")
        yield UInt32(self, "data_len", "param_data used bytes")
        yield UInt32(self, "data_max_len", "param_data total bytes")
        yield UInt32(self, "data_offset", "param_data offset (relative to start offset of data_table)")

class ParamSFO(Parser):
    PARSER_TAGS = {
        "id": "param_sfo",
        "category": "game",
        "file_ext": ("sfo",),
        "min_size": 14 * 8,
        "description": "SFO (System File Object) used by Playstation",
    }

    endian = LITTLE_ENDIAN

    def validate(self):
        #Check the first 4 bytes
        return (self.stream.readBytes(0, 4) == "\x00PSF")

    def createFields(self):

        #header
        yield Header(self, "header")

        #index tables
        for i in range(0, self["header/tables_entries"].value):
            yield IndexTable(self, "index_table[]")

        #jump to the keytable start
        keytable_start = self["header/keytable_start"].value
        if (keytable_start * 8) > self.current_size:
            yield self.seekByte(keytable_start, relative=False, null=True)

        #key tables
        for i in range(0, self["header/tables_entries"].value):

            name_length = 0;
            #search for the string terminator
            while True:

                one_byte = self.stream.readBytes(self.current_size + (name_length * 8), 1)
                one_byte = ord(one_byte)
                if (one_byte == 0):
                    break;
                else:
                    name_length += 1

            yield String(self, "key_table[]", name_length + 1, "key name", strip="\0")

        #jump to the datatable start
        datatable_start = self["header/datatable_start"].value
        if (datatable_start * 8) > self.current_size:
            yield self.seekByte(datatable_start, relative=False, null=True)

        #data tables
        for i in range(0, self["header/tables_entries"].value):
            objectname = "index_table[%d]" % i
            index_entry = self[objectname]
            if index_entry["data_fmt"].value == 1028:
                 yield UInt32(self, "data_table[]", "data")
            elif index_entry["data_fmt"].value == 516:
                yield String(self, "data_table[]", index_entry["data_max_len"].value, "data", strip="\0")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

