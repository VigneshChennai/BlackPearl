#!/usr/bin/env python

# This file is part of BlackPearl.

#BlackPearl is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#BlackPearl is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import sys

import os


MIN_SUPPORTED_VERSION = (3, 4, 2)


def check_env():
    var_to_check = ['BLACKPEARL_HOME',
                    'BLACKPEARL_SHARE',
                    'BLACKPEARL_LIBS',
                    'BLACKPEARL_APPS',
                    'BLACKPEARL_TMP',
                    'BLACKPEARL_CONFIG',
                    'BLACKPEARL_DATA',
                    'BLACKPEARL_LOGS',
                    'BLACKPEARL_HOST_NAME',
                    'BLACKPEARL_DEFAULT_APPS',
                    'WEBBIND',
                    'PYTHON',
                    'NGINX',
                    'UWSGI'
    ]
    for var in var_to_check:
        try:
            os.environ[var]
        except:
            msg = "%s env variable is not set." % (var)
            print("ERROR: " + msg)
            raise Exception(msg)


def check_python():
    python_bin = os.environ['PYTHON']
    if not os.path.isfile(python_bin):
        msg = "PYTHON variable set to invalid location '%s'" % (python_bin)
        print("ERROR: " + msg)
        raise Exception(msg)

    if not os.access(python_bin, os.X_OK):
        msg = "Python at '%s' location not executable by current user" % (
            python_bin)
        print("ERROR: " + msg)
        raise Exception(msg)

    version = sys.version_info
    version_num = version[0] * 1000000 + version[1] * 10000 + version[2] * 10
    MIN_SUPPORTED_VERSION_NUM = (MIN_SUPPORTED_VERSION[0] * 1000000
                                 + MIN_SUPPORTED_VERSION[1] * 10000
                                 + MIN_SUPPORTED_VERSION[2] * 10)

    if version_num < MIN_SUPPORTED_VERSION_NUM:
        err_msg = "Min python version supported is " \
                  "'%s.%s.%s', but current version is '%s.%s.%s'" % (
                      MIN_SUPPORTED_VERSION[0], MIN_SUPPORTED_VERSION[1],
                      MIN_SUPPORTED_VERSION[2],
                      version[0], version[1], version[2])
        print("ERROR: " + err_msg)
        raise Exception(err_msg)


def check_all():
    #check_env()
    #check_python()
    pass

    
