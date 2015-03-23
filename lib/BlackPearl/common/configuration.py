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


import yaml
import os
import base64

# Hardcoded defaults
config = {
    "path": {
        "lib": "/usr/lib/blackpearl",
        "share": "/usr/share/blackpearl",
        "webapps": [
            "/usr/share/blackpearl/builtinapps"
            "/usr/share/blackpearl/webapps"
        ],
        "run": "/run/blackpearl",
        "log": "/var/log/blackpearl"
    },

    "server": {
        "nginx": "/usr/sbin/nginx",
        "uwsgi": "/usr/sbin/uwsgi"
    },

    "hostname": "localhost",

    "listen": "127.0.0.1:80",

    "security": {
        "block_size": 16,
        "auto_generate_key": True
    },

    "uwsgi_options": {
        "plugins": "python",
        "log-truncate": True
    }
}


def validate_and_update(loaded_config):
    category = ["path", "server", "hostname", "listen", "security", "uwsgi_options"]

    for key in loaded_config.keys():
        if key not in category:
            raise ValueError("Unknown category '<%s>' in configuration file." % key)

    path = ["lib", "share", "webapps", "run", "log"]
    try:
        path_dict = loaded_config['path']
    except KeyError:
        loaded_config['path'] = config['path'].copy()
    else:
        for key in path_dict.keys():
            if key not in path:
                raise ValueError("Unknown value '<%s>' under category <path> in configuration file." % key)

        c = config['path'].copy()
        c.update(path_dict)

        cwd = os.getcwd()

        for i in ('lib', 'share', 'run', 'log'):
            if not c[i].startswith("/"):
                c[i] = os.path.join(cwd, c[i])
        t_list = []
        for i in c['webapps']:
            if i.startswith("/"):
                t_list.append(i)
            else:
                t_list.append(os.path.join(cwd, i))
        c['webapps'] = t_list
        loaded_config['path'] = c

    server = ["nginx", "uwsgi"]
    try:
        server_dict = loaded_config['server']
    except KeyError:
        loaded_config['server'] = config['server'].copy()
    else:
        for key in server_dict.keys():
            if key not in server:
                raise ValueError("Unknown value '<%s>' under category <server> in configuration file." % key)

        c = config['server'].copy()
        c.update(server_dict)
        loaded_config['server'] = c

    security = ["block_size", "auto_generate_key", "key"]
    try:
        security_dict = loaded_config['security']
    except KeyError:
        loaded_config['security'] = config['security'].copy()
    else:
        for key in security_dict.keys():
            if key not in security:
                raise ValueError("Unknown value '<%s>' under category <security> in configuration file." % key)

        c = config['security'].copy()
        c.update(security_dict)
        loaded_config['security'] = c

        if c['auto_generate_key']:
            c['key'] = base64.b64encode(os.urandom(c['block_size']))
        else:
            try:
                c['key']
            except:
                raise ValueError("Key is not defined under category <security> in configuration file." % key) from None

    try:
        loaded_config['hostname']
    except KeyError:
        loaded_config['hostname'] = config['hostname']

    try:
        loaded_config['listen']
    except KeyError:
        loaded_config['listen'] = config['listen']

    try:
        uwsgi_option_dict = loaded_config['uwsgi_options']
    except KeyError:
        loaded_config['uwsgi_options'] = config['uwsgi_options'].copy()
    else:
        c = config['uwsgi_options'].copy()
        c.update(uwsgi_option_dict)
        loaded_config['uwsgi_options'] = c


def load(path):
    with open(path) as file:
        loaded_config = yaml.load(file)
        validate_and_update(loaded_config=loaded_config)

    return loaded_config