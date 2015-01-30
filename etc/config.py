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

import platform

if platform.linux_distribution()[0] in ('arch',):
    # TODO: Need to add the list of distribution using python3 as default
    uwsgi_options = {
        'plugins': 'python',
        'log-truncate': 'true'
    }
else:
    uwsgi_options = {
        'plugins': 'python3',
        'log-truncate': 'true'
    }