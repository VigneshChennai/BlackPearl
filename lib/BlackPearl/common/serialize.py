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
import functools
import logging

logger = logging.getLogger(__name__)


class Serialize:
    def __init__(self):
        self.__serializable__ = True
        
    def to_json(self):
        return self.__dict__


def dumper(obj, skip_non_serializable=False):
    if skip_non_serializable:
        try:
            return obj.to_json()
        except:
            return "NonSerializable object"
    else:
        return obj.to_json()


def dumps(obj, skip_non_serializable=False):
    try:
        return json.dumps(obj, default=functools.partial(dumper, skip_non_serializable=skip_non_serializable), sort_keys=True)
    except:
        raise ValueError("The object <%s> is not Serializable." % obj) from None


def dump(obj, json_file, skip_non_serializable=False):
    try:
        return json.dump(obj, json_file, default=functools.partial(dumper, skip_non_serializable=skip_non_serializable),
                         sort_keys=True)
    except:
        raise ValueError("The object <%s> is not Serializable." % obj) from None


def loader(dictionary):
    if "__serializable__" in dictionary.keys():
        o = Serialize()
        for key, value in dictionary.items():
            setattr(o, key, value)
        return o
    return dictionary


def loads(json_string):
    return json.loads(json_string, object_hook=loader)


def load(json_file):
    return json.load(json_file, object_hook=loader)






