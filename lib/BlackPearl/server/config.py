#!/usr/bin/env python

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

import pwd

from os import getuid
from os.path import dirname, realpath, join

_options = ['home', 'share', 'lib', 'webapps', 'adminapps', 'defaultapps',
            'temp', 'logs', 'hostname', 'nginx', 'uwsgi',
            'listen', 'security_key', 'security_block_size']

home = dirname(dirname(dirname(dirname(realpath(__file__)))))
share = join(home, 'share')
lib = join(home, 'lib')
webapps = join(home, 'webapps')
adminapps = join(share, 'adminapps')
defaultapps = join(share, 'builtinapps')
temp = '/tmp/BlackPearl-' + pwd.getpwuid(getuid())[0]
logs = join(temp, 'logs')

nginx = 'nginx'
uwsgi = 'uwsgi'
hostname = 'localhost'
listen = '127.0.0.1:8080'

security_key = "asdf2345sdfghhjk"
security_block_size = 16
