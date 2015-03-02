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


import json


class Serialize:

    def to_json(self):
        setattr(self, "__serialized__", True)
        return self.__dict__


def dumper(obj):
    return obj.to_json()


def dumps(obj):
    try:
        return json.dumps(obj, default=dumper, sort_keys=True)
    except:
        raise ValueError("The object <%s> is not Serializable." % obj) from None


def dump(obj, json_file):
    try:
        return json.dump(obj, json_file, default=dumper, sort_keys=True)
    except:
        raise ValueError("The object <%s> is not Serializable." % obj) from None


def loader(dictionary):
    if "__serialized__" in dictionary.keys():
        o = Serialize()
        for key, value in dictionary.items():
            setattr(o, key, value)
        return o
    return dictionary


def loads(json_string):
    return json.loads(json_string, object_hook=loader)


def load(json_file):
    return json.load(json_file, object_hook=loader)
