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

from BlackPearl.core import datatype
from BlackPearl.core.decorators import weblocation, webname


@weblocation("/servertesting")
class Session:
    @webname("sessiontest")
    def testing(self, value):
        try:
            ret = {"session": self.session.value}
            self.session.value = value
        except AttributeError:
            self.session.value = value
            ret = {"session": None}

        return ret

    @webname("integerparamtest")
    def intergerparamtest(self, value: datatype.Integer()):
        return "Valid data <%s>" % value

    @webname("floatparamtest")
    def floatparamtest(self, value: datatype.Float()):
        return "Valid data <%s>" % value

    @webname("optionparamtest")
    def optionparamtest(self, value: datatype.Options("Male", "Female")):
        return "Valid data <%s>" % value

    @webname("formatparamtest")
    def formatparamtest(self, value: datatype.Format("^[a-zA-Z ,.'-]+$")):
        return "Valid data <%s>" % value

    @webname("integerlistparamtest")
    def integerlistparamtest(self, value: datatype.IntegerList()):
        return "Valid data <%s>" % value

    @webname("floatlistparamtest")
    def floatlistparamtest(self, value: datatype.FloatList()):
        return "Valid data <%s>" % value

    @webname("optionlistparamtest")
    def optionlistparamtest(self, value: datatype.OptionsList("Male", "Female")):
        return "Valid data <%s>" % value

    @webname("formatlistparamtest")
    def formatlistparamtest(self, value: datatype.FormatList("^[a-zA-Z ,.'-]+$")):
        return "Valid data <%s>" % value

    @webname("htmlfileoutputtest")
    def htmlfileoutputtest(self):
        yield ("Content-Type", "text/html")
        yield "<!DOCTYPE html>\n<html><head> <meta charset='UTF-8'><title>File output</title></head>" \
              "<body><h2>fileoutput testing</h2></body></html>".encode("UTF-8")

    @webname("fileinputtest")
    def fileinput(self, file:datatype.File(), value):
        few_bytes = file['file'].read(500);
        try:
            data = few_bytes.decode('UTF-8')
        except:
            data = "Binary File"
        return {
            "file": data,
            "value": value
        }