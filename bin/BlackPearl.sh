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

usage () {
    cat << EOF

**Usage**

Syntax: BlackPearl.sh <option>

Options:
    1. startup
    2. shutdown

EOF

}

if [ "$#" != 1 ]
then
    usage;
    exit -1
fi

CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$CURDIR/config.sh"

if [ -e $BLACKPEARL_TMP/BlackPearl.pid ]
then
    BLACKPEARL_PID=$(cat $BLACKPEARL_TMP/BlackPearl.pid)
fi

if [ "$1" == "shutdown" ]
then
    echo
    echo "Stopping BlackPearl services in localhost"\
         "running on <$USER> user account"

    if [ -e "$BLACKPEARL_TMP" ]
    then
        echo -n "Trying to stop BlackPearl service ..."
        if [ $BLACKPEARL_PID"x" == "x" ]
        then
            echo " [Failed] BlackPearl service is not currently running"

        elif ! kill $BLACKPEARL_PID > /dev/null 2>&1;
        then
            echo " [Failed] Unable to stop BlackPearl service. May be it is already stopped."
        else
            echo " [Stopped]"
        fi
    else
        echo "BlackPearl service is not running."
        exit 0
    fi

    exit 0

elif [ "$1" == "startup" ]
then
    if [ -e "$BLACKPEARL_TMP" ]
    then
        if kill -0 $BLACKPEARL_PID > /dev/null 2>&1;
        then
            echo "BlackPearl is currently running. "\
                 "Shutdown it before starting it up again."
            exit -1
        fi
    fi

    mkdir -p "$BLACKPEARL_TMP"
    rm -rf $BLACKPEARL_TMP/* > /dev/null 2>&1;
    mkdir -p "$BLACKPEARL_LOGS"
    touch "$BLACKPEARL_TMP/uwsgi_work_reload.file"
    echo "Starting BlackPearl server ..."
    $PYTHON "$BLACKPEARL_HOME"/bin/appserver_start.py --daemon
    echo
    echo "Log files are generated at <$BLACKPEARL_LOGS>"
    echo
else
    echo
    echo "Invalid option : $1"
    usage;
    exit -1
fi
