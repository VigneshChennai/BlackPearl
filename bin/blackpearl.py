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
import os
import shutil
import pwd
import traceback
import signal

from BlackPearl.server import appserver, config

def usage():
    print("""**Usage**

Syntax: blackpearl.py <option>

Options:
    1. startup
    2. shutdown""")

def startserver(daemon):
    pypath = [config.lib,
              config.webapps,
              config.adminapps,
              config.defaultapps]
    os.environ["PYTHONPATH"] = ":".join(pypath)
    sys.path.extend(pypath)
    if os.access(config.temp, os.F_OK):
        try:
            with open(os.path.join(config.temp, "BlackPearl.pid")) as f:
                pid = f.read()
            os.kill(int(pid), 0)
            print("BlackPearl is currently running. "\
                  "Shutdown it before starting it up again.")
            return
        except:
            pass

        shutil.rmtree(config.temp)

    os.mkdir(config.temp)
    os.mkdir(config.logs)
    os.mkdir(os.path.join(config.temp, 'pickle'))
    open(os.path.join(config.temp,"uwsgi_worker_reload.file"), "w").close()
    print("\nStarting BlackPearl server ...")
    print("Generating log files at %s" % config.logs)
    appserver.start(daemon)


def stopserver():
    print("\nStopping BlackPearl services in localhost"\
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
            startserver(daemon=True)
        elif sys.argv[1] == "shutdown":
            stopserver()
        else:
            print("Invalid arguments passes. <%s>" % sys.argv[1:])
            usage()
    else:
        print("Invalid arguments passes. <%s>" % sys.argv[1:])
        usage()


    
