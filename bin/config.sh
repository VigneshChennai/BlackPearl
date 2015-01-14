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


export BLACKPEARL_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..&& pwd )"

export BLACKPEARL_SHARE="$BLACKPEARL_HOME/share"
export BLACKPEARL_LIBS="$BLACKPEARL_HOME/lib"
export BLACKPEARL_APPS="$BLACKPEARL_HOME/webapps"
export BLACKPEARL_ADMIN_APPS="$BLACKPEARL_SHARE/AdminApps"
export BLACKPEARL_DEFAULT_APPS="$BLACKPEARL_SHARE/builtinapps"
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

export PYTHONPATH="$PYTHONPATH:$BLACKPEARL_LIBS:$BLACKPEARL_APPS:$BLACKPEARL_DEFAULT_APPS"

export BLOCK_SIZE=16
export SESS_AES_KEY="asdf2345sdfghhjk"

