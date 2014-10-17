#!/bin/bash

export DARKCHOCO_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export DARKCHOCO_APPS="$DARKCHOCO_HOME/webapps"

#export DARKCHOCO_TMP="/tmp/darkchoco-`date +%s`-$RANDOM"
export DARKCHOCO_TMP="/tmp/darkchoco-$USER"
export DARKCHOCO_LOGS="$DARKCHOCO_TMP/logs-`date +%s`"
export DARKCHOCO_SERVER_NAME='localhost'

export NGINX="nginx"
export UWSGI="uwsgi"

export WEBPORT=8080
export APPPORT=9090
export PROC_PER_APP="4"
export THREAD_PER_PROC="2"
 
