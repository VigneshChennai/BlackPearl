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

import sys
import os
import shutil
import pwd
import traceback
import signal

from BlackPearl.server import appserver, config

startup_notes = """
    BlackPearl is free software. License GPLv3+: GNU GPL version 3 or later
    <http://gnu.org/licenses/gpl.html>

    "Free software" means software that respects users' freedom and community.
    Roughly, it means that the users have the freedom to run, copy, distribute,
    study, change and improve the software. Thus, "free software" is a matter
    of liberty, not price. To understand the concept, you should think of
    "free" as in "free speech," not as in "free beer".
    For details, visit https://www.gnu.org/philosophy/free-sw.html
"""

author = """
    Written by Vigneshwaran P (https://github.com/VigneshChennai)
"""


class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARK_CYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def usage():
    print("""Usage:

Syntax: blackpearl.py <option>

Options:
    1. startup
    2. shutdown""")


def start_server(daemon):
    print(Color.BOLD + '\nBlackPearl' + Color.END)
    print(startup_notes)
    print(Color.BOLD + 'Author' + Color.END)
    print(author)

    if os.access(config.temp, os.F_OK):
        try:
            with open(os.path.join(config.temp, "BlackPearl.pid")) as f:
                pid = f.read()
            os.kill(int(pid), 0)
            print("BlackPearl is currently running. "
                  "Shutdown it before starting it up again.\n")
            return
        except:
            pass

        shutil.rmtree(config.temp)

    os.mkdir(config.temp)
    os.mkdir(config.logs)
    os.mkdir(os.path.join(config.temp, 'pickle'))
    open(os.path.join(config.temp, "uwsgi_worker_reload.file"), "w").close()
    print("\nStarting BlackPearl server ...")
    print("Generating log files at %s" % config.logs)
    appserver.start(daemon)


def stop_server():
    print("Stopping BlackPearl services in localhost "
          "running on <%s> user account" % pwd.getpwuid(os.getuid())[0])
    if os.access(config.temp, os.F_OK):
        print("Trying to stop BlackPearl service ...", end="")
        try:
            with open(os.path.join(config.temp, "BlackPearl.pid")) as f:
                pid = f.read()
        except:
            print(traceback.format_exc())
            print(" [Failed] BlackPearl service is not currently running")
            return
        else:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except:
                print(" [Failed] Unable to stop BlackPearl service. May be it is already stopped.")
                return
            else:

                print(" [Stopped]")
                return
    else:
        print("BlackPearl service is not running.")
        return

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] == "startup":
            start_server(daemon=True)
        elif sys.argv[1] == "shutdown":
            stop_server()
        else:
            print("Invalid arguments passes. <%s>" % sys.argv[1:])
            usage()
    else:
        print("Invalid arguments passes. <%s>" % sys.argv[1:])
        usage()