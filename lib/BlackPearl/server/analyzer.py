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
import logging

from pip import basecommand

logger = logging.getLogger()


def _upgrade_pip():
    if pip.main(['install', "--upgrade", "pip"]) == 1:
        logger.error("Failed to upgrade pip in the virtualenv.")
        sys.exit(1)


def _install():
    for package in ('PyYaml', 'pycrypto', 'requests'):
        if pip.main(['install', package]) == 1:
            logger.error("Failed to install package<%s> in the new virtualenv." % package)
            sys.exit(1)


# Analyses the single webapp folder
def analyser(webapps_pickle_minimal, pickle_folder, location, folder):
    from BlackPearl.core.webapps import WebAppMinimal
    from BlackPearl.core import webapps as webapps

    if not os.access(webapps_pickle_minimal, os.F_OK):
        webapps_minimal = []
    else:
        with open(webapps_pickle_minimal, "rb") as rb:
            webapps_minimal = pickle.load(rb)

    try:
        logger.info("Analysing webapp <%s> ...." % folder)
        # Analysing the webapp folder and returning the analysis result
        webapp = webapps.analyze(location, folder)
        logger.info("Webapp analysing completed.")
        logger.info("Webapp details : %s" % webapp)

        # Pickling the webapp information
        f = os.path.join(pickle_folder, webapp.id + ".pickle")
        logger.info("Writing analysed information to file <%s>." % f)
        with open(f, "wb") as pickle_file:
            pickle.dump(webapp, pickle_file)
        logger.info("Write completed")

        webapp_minimal = WebAppMinimal(webapp, f)
        webapp_minimal.python_home_path = sys.exec_prefix
        webapp_minimal.python_path = sys.executable
        webapps_minimal.append(webapp_minimal)

        with open(webapps_pickle_minimal, "wb") as f:
            pickle.dump(webapps_minimal, f)
    except:
        logger.error("Fatal error during analysing webapps.")
        logger.error("%s" % traceback.format_exc())


def main():
    webapps_pickle_minimal = sys.argv[1]
    pickle_folder = sys.argv[2]
    webapps_location = sys.argv[3]
    webapp_folder = sys.argv[4]

    log_level = int(sys.argv[5])
    log_format = sys.argv[6]

    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(log_format))
    logger.addHandler(ch)

    logger.info("Going to install basic required packages by blackpearl.")

    # pip is removing our log handler and initializing their own handlers.
    # I am just stopping their logger initialization using below code. It is the worst way to do it but it works.
    # TODO: Need to find a cleaner way
    basecommand.logging_dictConfig = lambda *args, **kwargs: None
    _upgrade_pip()
    _install()

    logger.info("Packages installed successfully.")

    analyser(webapps_pickle_minimal, pickle_folder, webapps_location, webapp_folder)


if __name__ == "__main__":
    main()