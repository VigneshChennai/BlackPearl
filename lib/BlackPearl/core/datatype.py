#!/usr/bin/env python

# This file is part of BlackPearl.

# BlackPearl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BlackPearl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import re


def isvalid(datatype, data):
    """Function to validate the data passed in the request."""
    try:
        return datatype.__is_valid__(data)
    except AttributeError as ae:
        raise Exception("DataType <" + str(datatype.__class__.__name__)
                        + "> is a invalid to be used in web "
                        + "method annotations.\nActual error: " + str(ae))


def parse(datatype, data):
    if data.file:
        if not isinstance(datatype, File):
            raise Exception("%s, but <File datatype> is given." % (str(datatype)))
    if isvalid(datatype, data):
        return datatype.__parse__(data)
    else:
        raise Exception("%s, but <%s> is given." % (str(datatype), str(data.value)))


class Type:
    """All the data type should be a subclass of this class"""
    def __is_valid__(self, data):
        return True

    def __parse__(self, data):
        return data


class ListType(Type):
    """All the list datatype should be a subclass of this class"""
    pass


class File(Type):
    def __is_valid__(self, data):
        if data.file:
            return True
        else:
            return False

    def __parse__(self, data):
        return {
            "file": data.file,
            "filename": data.filename,
            "filetype": data.type
        }

    def __repr__(self):
        return "File datatype"

    def __str__(self):
        return "It accepts only file inputs."


class FileList(ListType, File):
    def __repr__(self):
        return "File List datatype"


class Float(Type):
    def __is_valid__(self, data):
        try:
            float(data.value)
            return True
        except:
            return False

    def __parse__(self, data):
        return float(data.value)

    def __repr__(self):
        return "Float datatype"

    def __str__(self):
        return "It accepts floating point number. Example : 234.123"


class FloatList(ListType, Float):
    def __repr__(self):
        return "Float List datatype"


class Integer(Type):
    def __is_valid__(self, data):
        try:
            int(data.value)
            return True
        except:
            return False

    def __parse__(self, data):
        return int(data.value)

    def __repr__(self):
        return "Integer datatype"

    def __str__(self):
        return "It accepts only non floating point number. Example : 234"


class IntegerList(ListType, Integer):
    def __repr__(self):
        return "Integer List datatype"


class Format(Type):
    """Custom regex based format"""

    def __init__(self, data_format):
        self.data_format = data_format
        self.pattern = re.compile(data_format)

    def __is_valid__(self, data):
        try:
            if self.pattern.match(data.value):
                return True
            else:
                return False
        except:
            return False

    def __parse__(self, data):
        return data.value

    def __repr__(self):
        return "Regex datatype"

    def __str__(self):
        return "It is defined to accept only value of " \
               "format <%s> as value" % (str(self.pattern))


class FormatList(ListType, Format):
    def __init__(self, data_format):
        Format.__init__(self, data_format)

    def __repr__(self):
        return "Regex List datatype"


class Options(Type):
    def __init__(self, *values):
        v = []
        for value in values:
            v.append(str(value))
        self.values = v

    def __is_valid__(self, data):
        try:
            if data.value in self.values:
                return True
            else:
                return False
        except:
            return False

    def __parse__(self, data):
        return data.value

    def __repr__(self):
        return "Option datatype"

    def __str__(self):
        return "It is defined to accept only one of the <%s> as value" % (str(self.values))


class OptionsList(ListType, Options):
    def __init__(self, *values):
        Options.__init__(self, values)

    def __repr__(self):
        return "Option List datatype"
