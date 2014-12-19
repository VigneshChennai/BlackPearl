#!/usr/bin/python

import os
import re
import subprocess
import sys

MIN_SUPPORTED_VERSION = (3,4,2)

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
                    'APPBIND',
                    'WEBBIND',
                    'BLOCK_SIZE',
                    'SESS_AES_KEY',
                    'PYTHON',
                    'NGINX',
                    'UWSGI',
                    'ENV'
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

    if  version_num < MIN_SUPPORTED_VERSION_NUM:
        err_msg = "Min python version supported is "\
                    "'%s.%s.%s', but current version is '%s.%s.%s'" % (
                        MIN_SUPPORTED_VERSION[0],MIN_SUPPORTED_VERSION[1],
                        MIN_SUPPORTED_VERSION[2],
                        version[0], version[1], version[2])
        print("ERROR: " + err_msg)
        raise Exception(err_msg)
        
def check_all():
    check_env()
    check_python()
    
    
