#!/bin/bash

usage () {
    cat << EOF
    
**Usage**

Syntax: darkchoco.sh <option>

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
source $CURDIR/config.sh

if [ -e $DARKCHOCO_TMP/darkchoco.pid ]
then
    DARKCHOCO_PID=$(cat $DARKCHOCO_TMP/darkchoco.pid)
fi

if [ "$1" == "shutdown" ]
then
    echo
    echo "Stopping Darkchoco services in localhost"\
         "running on <$USER> user account"
         
    if [ -e "$DARKCHOCO_TMP" ]
    then
        echo -n "Trying to stop darkchoco service ..."
        if [ $DARKCHOCO_PID"x" == "x" ]
        then
            echo " [Failed] darkchoco service is not currently running"
            
        elif ! kill $DARKCHOCO_PID > /dev/null 2>&1;
        then
            echo " [Failed] Unable to stop darkchoco service. May be it is already stopped."
        else
            echo " [Stopped]"
        fi
    else
        echo "Darkchoco service is not running."
        exit 0
    fi
    
    exit 0
    
elif [ "$1" == "startup" ]
then
    if [ -e "$DARKCHOCO_TMP" ]
    then
        if kill -0 $DARKCHOCO_PID > /dev/null 2>&1;
        then
            echo "Darkchoco is currently running. "\
                 "Shutdown it before starting it up again."
            exit -1
        fi
    fi
    
    mkdir -p "$DARKCHOCO_TMP"
    mkdir -p "$DARKCHOCO_LOGS"

    rm -f $DARKCHOCO_TMP/* > /dev/null 2>&1;
    echo "Starting darkchoco server ..."
    $PYTHON "$DARKCHOCO_LIBS"/server/appserver.py --daemon
    echo
    echo "Log files are generated at <$DARKCHOCO_LOGS>"
    echo
else
    echo
    echo "Invalid option : $1"
    usage;
    exit -1
fi
