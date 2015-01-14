#!/bin/bash

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
#along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

usage() {
    echo
    echo "***Comman usage*** : newapp.sh"
    echo ""
    echo "    newapp.sh <appname>"
    echo ""
    echo "Example :"
    echo "    newapp.sh mynewapp"
    echo ""
}

if [ "$1"x == x ]
then
    usage
    exit 1
fi


APPNAME="$1"
echo -n "Application Full Name : "
read APPFULLNAME
echo -n "Author Name : "
read AUTHNAME
echo -n "Website : "
read WEBSITE
echo -n "Email Address : "
read EMAILID

mkdir "$APPNAME"

cd "$APPNAME"

cat > config.py <<EOF
#!/bin/env python

################################################################################
#                  BlackPearl Application configuration file
#
# Application Name : $APPFULLNAME
# Author :  $AUTHNAME
# Website : $WEBSITE
# Email Address : $EMAILID
#
################################################################################


name= "$APPFULLNAME"

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

url_prefix="$APPNAME"

#Handlers are the list of python files which holds the python web modules.
#
#The functions which are using @weblocation decorate but not in the below listed
#python files will be ignored.
#
#Example : if python file is (Webapp/hander.py)
#then
#handlers = ['Webapp.hander']

handlers = ["$APPNAME.handlers"]

#If sessions are not used in the application, the below should be set to False
session_enabled = True


#List of python function which need to process the incoming request before
#handing it to the webmodules
#
#This is not the python files, it should the list of fulle python function name
#
#Example : if python function "preprocessor" listed under Webapp/hander.py file
#then
#posthanlder = ['Webapp.hander.preprocessor'}

preprocessors = []

#List of python function which need to process the outgoing request after
#the webmodules processed the request.
#
#This is not the python files, it should the list of full python function name
#
#Example : if python function "posthandler" listed under Webapp/hander.py file
#then
#posthanlder = ['Webapp.hander.posthandler'}

posthandlers = []

EOF

cat > handlers.py <<EOF
#!/bin/env python

from BlackPearl.core.decorators import weblocation

@weblocation("hello")
def hello():
    ret = {
            "msg" : "Hello world",
            "desc" : "My first helloworld BlackPearl web application"
    }
    return ret

EOF
