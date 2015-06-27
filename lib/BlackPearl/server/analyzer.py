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
import sys
import pickle
import traceback
import pip

from BlackPearl.server.core.logger import Logger

# Initializing logger
logger = Logger(Logger.DEBUG)
logger.initialize()


for package in ('PyYaml', 'pycrypto'):
    if pip.main(['install', package]) == 1:
        print("ERROR: Failed to install package<%s> in the new virtualenv." % package)
        sys.exit(1)
    else:
        print("INFO: Packages installed successfully.")

from BlackPearl.core.webapps import WebAppMinimal
from BlackPearl.core import webapps as webapps

# Analyses the single webapp folder
def analyser(webapps_pickle_minimal, pickle_folder, location, folder):

    if not os.access(webapps_pickle_minimal, os.F_OK):
        webapps_minimal = []
    else:
        with open(webapps_pickle_minimal, "rb") as rb:
            webapps_minimal = pickle.load(rb)

    try:
        print("INFO: Analysing webapp <%s> ...." % folder)
        # Analysing the webapp folder and returning the analysis result
        webapp = webapps.analyze(location, folder)
        print("INFO: Webapp analysing completed.")
        print("INFO: Webapp details : %s" % webapp)

        # Pickling the webapp information
        f = os.path.join(pickle_folder, webapp.id + ".pickle")
        print("INFO: Writing analysed information to file <%s>." % f)
        with open(f, "wb") as pickle_file:
            pickle.dump(webapp, pickle_file)
        print("INFO: Write completed")

        webapp_minimal = WebAppMinimal(webapp, f)
        webapp_minimal.python_home_path = sys.exec_prefix
        webapp_minimal.python_path = sys.executable
        webapps_minimal.append(webapp_minimal)

        with open(webapps_pickle_minimal, "wb") as f:
            pickle.dump(webapps_minimal, f)
    except:
        print("ERROR: Fatal error during analysing webapps.")
        print("ERROR: %s" % traceback.format_exc())


def main():
    webapps_pickle_minimal = sys.argv[1]
    pickle_folder = sys.argv[2]
    webapps_location = sys.argv[3]
    webapp_folder = sys.argv[4]

    analyser(webapps_pickle_minimal, pickle_folder, webapps_location, webapp_folder)


if __name__ == "__main__":
    main()