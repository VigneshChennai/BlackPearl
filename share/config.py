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
import base64

from os.path import dirname, realpath, join

home = dirname(dirname(realpath(__file__)))
share = join(home, 'share')

lib = join(home, 'lib')
adminapps = join(share, 'adminapps')
builtinapps = join(share, 'builtinapps')
webapps = join(share, 'webapps')

run = join(home, 'run')
logs = join(home, join('var', 'logs'))

nginx = '/usr/sbin/nginx'
uwsgi = '/usr/sbin/uwsgi'
hostname = 'localhost'
listen = '127.0.0.1:8080'

security_block_size = 16
security_key = base64.b64encode(os.urandom(security_block_size))

uwsgi_options = {
    'plugins': 'python',
    'log-truncate': 'true'
}

builtinapps_enabled = True
adminapps_enabled = True