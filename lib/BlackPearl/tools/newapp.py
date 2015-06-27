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

import os
import sys


def usage():
    print("""
Usage : newapp

    newapp <appname>

Example :
    newapp my_new_app
""")

config_file = """
########################################################################################################################
#                                    BlackPearl Application configuration file
#
# Full Name = "{fullappname}"
# Author = "{author}"
# Website = "{website}"
# Email ID = "{emailid}"
#
########################################################################################################################

name : {fullappname}

# Description: Application Name.
# Example : name = "My First BlackPearl Application"
# Optional: Yes (if not specified: The folder name will be used as application name)

desc : ''

url_prefix : /{appname}

# Description: URL Prefix for the web application.
# Example : url_prefix = "/reservation"
# Optional: Yes (if not specified: The folder name will be used as url_prefix)
#
# Note:
#       1. url_prefix should start with '/'. If not, '/' will be automatically prefixed to it with a warning while the
#          server starts.
#       2. if url_prefix : / then the application will be deployed as root application.
#

handlers :
    - handlers

# Description: Handlers are the list of python modules which holds the blackpearl web modules.
#
# Example : if python file is (Webapp_folder/src/api/handlers.py and in Webapp_folder/src/api/security/handlers.py) then
#           handlers :
#                - handler
#                - security.handlers
#
# Note: Each blackpearl web modules decorated with @weblocation decorate but not defined in the below python modules
#       will be ignored
#

session_enabled : true

# Description: Enables or disables session feature in the webapp.
#
# Example : session_enabled : true

# Note:
#       1. Session are saved in the user browser cookie.
#       2. Sessions are encrypted before saving in cookie, so it safe to save data which are sensitive but try to void
#          saving sensitive data in session.
#       3. Always store less amount of data in session, since it is saved in cookie, server will throw error when
#          storing large data (For example: you can store a string data of size ~2840 bytes maximum).
#

preprocessors : []

# Description: List of python function which need to process the incoming request before handing it to the web modules.
# Example : if preprocessor python functions (ie. functions decorated with @preprocessor decorator)
#           "access_check" and "unique_user_count" defined under Webapp_folder/src/api/preprocessors.py file then
#
#           preprocessors :
#                  - preprocessors.access_check
#                  - preprocessors.unique_user_count
#
# Optional: Yes
#
# Note: preprocessors list defined here is for specifying the order of execution only. The python function must be
#       decorated with @preprocessor to define it as preprocessor

posthandlers : []

# Description: List of python function which need to process the outgoing data after the web module handled the request.
# Example : if posthandler python functions (ie. functions decorated with @posthandler decorator)
#           "data_validation_filter" and "data_formatting" defined under Webapp_folder/src/api/posthandlers.py file then
#
#           preprocessors :
#                  - posthandlers.data_validation_filter
#                  - posthandlers.data_formatting
#
# Optional: Yes
#
# Note: Posthandlers list defined here is for specifying the order of execution only. The python function must be
#       decorated with @posthandler to define it as posthandler
"""

handlers_file = """#!/usr/bin/env python

from BlackPearl.core import datatype
from BlackPearl.core.decorators import weblocation


@weblocation("helloworld")
def helloworld():
    ret = {
            "msg" : "Hello world",
            "desc" : "My first hello world BlackPearl web application"
    }
    return ret


@weblocation("/calculator")
def simple_calculator(operation: datatype.Options("add", "sub", "mul", "div"),
                      value1: datatype.Float(),
                      value2: datatype.Float()):
    if operation == "add":
        return value1 + value2
    elif operation == "sub":
        return value1 - value2
    elif operation == "mul":
        return value1 * value2
    else:
        return value1 / value2
"""


def invoke(**args):

    # if len(args) != 2:
    #    usage()

    if not os.access(".", os.W_OK):
        print("ERROR: Unable to create folder on the current working directory")
        raise Exception("Newapp creation failed.")

    app_name = args['newapp']
    full_app_name = input("Application Full Name : ")
    author = input("Author Name : ")
    website = input("Website : ")
    email_id = input("Email Address : ")

    os.mkdir(app_name)
    os.mkdir(os.path.join(app_name, "lib"))
    os.mkdir(os.path.join(app_name, "src"))
    os.mkdir(os.path.join(app_name, "src/api"))
    os.mkdir(os.path.join(app_name, "src/static"))
    os.mkdir(os.path.join(app_name, "src/dynamic"))
    os.mkdir(os.path.join(app_name, "test"))

    with open(os.path.join(app_name, 'config.yaml'), "w") as f:
        f.write(config_file.format(appname=app_name,
                                   fullappname=full_app_name,
                                   author=author,
                                   website=website,
                                   emailid=email_id))

    with open(os.path.join(app_name, "src/api", 'handlers.py'), "w") as f:
        f.write(handlers_file)
