#!/bin/env python

#This file is part of BlackPearl.

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

import os
import sys

def usage():
    print("""
Usage : newapp

    newapp <appname>

Example :
    newapp mynewapp
""")

config_file = """#!/bin/env python

################################################################################
#                  BlackPearl Application configuration file
#
fullname = "{fullappname}"
author = "{author}"
website = "{website}"
email = "{emailid}"
#
################################################################################


name= "{appname}"

#URL Prefix for the webapplication.
#
#If it is not specifed, the foldername of the webapplication will be taken as
#url_prefix
#
#A url_prefix "ROOT" will make the application to hosted on the root level.
#
#Example :-
# if url_prefix="dwm"
# then the application will be deployed at "www.example.com/dwm"
#
# if url_prefix="ROOT"
# then the application will be deployed at "www.example.com"
#

url_prefix="{appname}"

#Handlers are the list of python files which holds the python web modules.
#
#The functions which are using @weblocation decorate but not in the below listed
#python files will be ignored.
#
#Example : if python file is (Webapp/hander.py)
#then
#handlers = ['Webapp.hander']

handlers = ["{appname}.handlers"]

#If sessions are not used in the application, the below should be set to False
session_enabled = True


#List of python function which need to process the incoming request before
#handing it to the webmodules.
#Note: The list defined here are for specifying the order of execution only.
#      The preprocessors must be decorate with @preprocessor decorator
#
#This is not the python files, it should the list of fulle python function name
#
#Example : if python function "preprocessor" listed under Webapp/hander.py file
#then
#preprocessor = ['Webapp.hander.preprocessor']

preprocessors = []

#List of python function which need to process the outgoing request after
#the webmodules processed the request.
#Note: The list defined here are for specifying the order of execution only.
#      The posthandler must be decorate with @posthandler decorator
#
#This is not the python files, it should the list of full python function name
#
#Example : if python function "posthandler" listed under Webapp/hander.py file
#then
#posthandler = ['Webapp.hander.posthandler']

posthandlers = []

"""

handlers_file = """
#!/bin/env python

from BlackPearl.core.decorators import weblocation

@weblocation("hello")
def hello():
    ret = {
            "msg" : "Hello world",
            "desc" : "My first helloworld BlackPearl web application"
    }
    return ret
"""

def main():

    if len(sys.argv) != 2:
        usage()
        sys.exit(1)

    if not os.access(".", os.W_OK):
        print("ERROR: Unable to create folder on the current working directory")
        sys.exit(1)

    appname = sys.argv[1]
    fullappname = input("Application Full Name : ")
    author = input("Author Name : ")
    website = input("Website : ")
    emailid = input("Email Address : ")

    os.mkdir(appname)
    with open(os.path.join(appname, 'config.py'), "w") as f:
        f.write(config_file.format(appname=appname,
                   fullappname=fullappname,
                   author=author,
                   website=website,
                   emailid=emailid)
               )

    with open(os.path.join(appname, 'handlers.py'), "w") as f:
        f.write(handlers_file)

if __name__ == "__main__":
    main()