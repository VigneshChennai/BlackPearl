#!/bin/bash

export BLACKPEARL_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..&& pwd )"

export BLACKPEARL_SHARE="$BLACKPEARL_HOME/share"
export BLACKPEARL_LIBS="$BLACKPEARL_HOME/lib"
export BLACKPEARL_APPS="$BLACKPEARL_HOME/webapps"
export BLACKPEARL_ADMIN_APPS="$BLACKPEARL_SHARE/AdminApps"
export BLACKPEARL_TMP="/tmp/BlackPearl-$USER"
export BLACKPEARL_DATA="/tmp/BlackPearl-$USER"
export BLACKPEARL_CONFIG="/tmp/BlackPearl-$USER"

#export BLACKPEARL_LOGS="$BLACKPEARL_TMP/logs-`date +%s`"
export BLACKPEARL_LOGS="$BLACKPEARL_TMP/logs"
export BLACKPEARL_HOST_NAME='localhost'

export PYTHON="`which python`"
export NGINX="nginx"
export UWSGI="uwsgi"

export WEBBIND="127.0.0.1:8080"
export APPBIND="$BLACKPEARL_TMP/uwsgi.sock"
 
export PYTHONPATH="$PYTHONPATH:$BLACKPEARL_LIBS"

export BLOCK_SIZE=16
export SESS_AES_KEY="asdf2345sdfghhjk"

#possible values, dev and prd
export ENV="dev"
