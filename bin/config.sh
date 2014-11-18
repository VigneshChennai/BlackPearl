#!/bin/bash

export DARKCHOCO_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..&& pwd )"

export DARKCHOCO_SHARE=$DARKCHOCO_HOME/share
export DARKCHOCO_LIBS=$DARKCHOCO_HOME/lib
export DARKCHOCO_APPS="$DARKCHOCO_HOME/webapps"
export DARKCHOCO_ADMIN_APPS="$DARKCHOCO_SHARE/AdminApps"
export DARKCHOCO_TMP="/tmp/darkchoco-$USER"
export DARKCHOCO_DATA="/tmp/darkchoco-$USER"
export DARKCHOCO_CONFIG="/tmp/darkchoco-$USER"

export DARKCHOCO_LOGS="$DARKCHOCO_TMP/logs-`date +%s`"
export DARKCHOCO_HOST_NAME='localhost'

export PYTHON="`which python`"
export NGINX="nginx"
export UWSGI="uwsgi"

export WEBBIND="127.0.0.1:8080"
export APPBIND="$DARKCHOCO_TMP/uwsgi.sock"
 
export PYTHONPATH="$PYTHONPATH:$DARKCHOCO_LIBS"

export BLOCK_SIZE=16
export SESS_AES_KEY="asdf2345sdfghhjk"
