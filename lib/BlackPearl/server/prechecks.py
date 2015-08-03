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

import sys
import logging

logger = logging.getLogger(__name__)

MIN_SUPPORTED_VERSION = (3, 4, 2)


def check_python():
    version = sys.version_info
    version_num = version[0] * 1000000 + version[1] * 10000 + version[2] * 10
    min_supported_version_num = (MIN_SUPPORTED_VERSION[0] * 1000000
                                 + MIN_SUPPORTED_VERSION[1] * 10000
                                 + MIN_SUPPORTED_VERSION[2] * 10)

    if version_num < min_supported_version_num:
        err_msg = "Min python version supported is " \
                  "'%s.%s.%s', but current version is '%s.%s.%s'" % (
                      MIN_SUPPORTED_VERSION[0], MIN_SUPPORTED_VERSION[1],
                      MIN_SUPPORTED_VERSION[2],
                      version[0], version[1], version[2])
        raise Exception(err_msg)


def check_all():
    check_python()