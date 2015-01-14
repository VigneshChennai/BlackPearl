#!/bin/env python

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


import sys

from BlackPearl.server import appserver

def usage():
    print("Usage:\n")
    print("appserver_start.py [-d or --daemon]")

if len(sys.argv) == 1:
    appserver.start(daemon=False)
elif len(sys.argv) == 2 and sys.argv[1] in ("--daemon", "-d"):
    appserver.start(daemon=True)
else:
    print("Invalid arguments passes. <%s>" % sys.argv)
