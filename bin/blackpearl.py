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
import time

from BlackPearl.server import appserver
from os.path import dirname, realpath

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

Syntax: blackpearl.py [-c config_path] <action>

Actions:
    1. startup
    2. shutdown""")


def start_server(daemon, config):

    if os.access(config.run, os.F_OK):
        try:
            with open(os.path.join(config.run, "BlackPearl.pid")) as f:
                pid = f.read()
            os.kill(int(pid), 0)
            print("BlackPearl is currently running. "
                  "Shutdown it before starting it up again.\n")
            return
        except:
            pass

        shutil.rmtree(config.run)

    os.mkdir(config.run)
    os.mkdir(os.path.join(config.run, 'uwsgi'))
    os.mkdir(os.path.join(config.run, 'nginx'))
    os.mkdir(os.path.join(os.path.join(config.run, 'uwsgi'), 'pickle'))
    if not os.access(config.logs, os.F_OK):
        os.makedirs(config.logs)
    if not os.access(os.path.join(config.logs, "uwsgi"), os.F_OK):
        os.makedirs(os.path.join(config.logs, "uwsgi"))

    # open(os.path.join(os.path.join(config.run, 'uwsgi'), "worker_reload.file"), "w").close()
    print("\nStarting BlackPearl server ...")
    print("Generating log files at %s" % config.logs)
    appserver.start(config, daemon)


def stop_server(config):
    print("Stopping BlackPearl services in localhost "
          "running on <%s> user account" % pwd.getpwuid(os.getuid())[0])
    if os.access(config.run, os.F_OK):
        print("Trying to stop BlackPearl service .", end="")
        sys.stdout.flush()
        try:
            with open(os.path.join(config.run, "BlackPearl.pid")) as f:
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
                try:
                    count = 0
                    while count < 15:
                        print(".", end="")
                        sys.stdout.flush()
                        os.kill(int(pid), 0)
                        time.sleep(1)
                        count += 1
                    print("[Failed]")
                except:
                    print("[Stopped]")
                return

    else:
        print("BlackPearl service is not running.")
        return


class Configuration:
    __options__ = [
        'home', 'share', 'lib', 'webapps', 'adminapps', 'builtinapps', 'run',
        'logs', 'hostname', 'nginx', 'uwsgi',
        'listen', 'security_key', 'security_block_size', 'uwsgi_options',
        'builtinapps_enabled', 'adminapps_enabled'
    ]

    __config_loc__ = [
        '/etc/blackpearl/config.py',
        '%s/etc/config.py' % dirname(dirname(realpath(__file__)))

    ]

    __default_config_loc__ = [
        '/usr/share/blackpearl/config.py',
        '%s/share/config.py' % dirname(dirname(realpath(__file__)))
    ]

    def __init__(self, config=None):
        default_config_loc = None
        for loc in Configuration.__default_config_loc__:
            if os.access(loc, os.F_OK):
                default_config_loc = loc
                break
        if default_config_loc:
            print("INFO: Using base configuration file at <%s> for initializing default values" % default_config_loc)
        else:
            print("SEVERE: Base configuration file not found!!")
            raise FileNotFoundError("Base configuration file not found!! ")

        l = {}
        g = {"__file__": default_config_loc}
        with open(default_config_loc) as file:
            exec(file.read(), l, g)

        config_loc = None
        if config:
            if os.access(config, os.F_OK):
                config_loc = config
            else:
                raise FileNotFoundError("Specified configuration file not found: <%s>" % config)
        else:
            for loc in Configuration.__config_loc__:
                if os.access(loc, os.F_OK):
                    config_loc = loc
                    break
        if config_loc:
            print("INFO: Using configuration file at <%s>" % config_loc)
            g['__file__'] = config_loc
            with open(config_loc) as file:
                exec(file.read(), l, g)
        else:
            print("WARNING: Configuration file not found. Using only base configuration file.")

        for option in Configuration.__options__:
            try:
                setattr(self, option, g[option])
            except KeyError:
                print("SEVERE: Option <%s> not defined in the configuration file" % option)
                raise NameError("Option <%s> not defined in the configuration file")


# used from https://gist.github.com/VigneshChennai/a79e84df57505d88c5b9
class ArgumentParserRules:

    def __init__(self, with_arguments, without_arguments,
                 should_not_be_with={}, should_be_with={},
                 with_repetitions={}, mandatory=[]):
        self.with_arguments = with_arguments
        self.without_arguments = without_arguments
        self.should_not_be_with = should_not_be_with
        self.should_be_with = should_be_with
        self.with_repetitions = with_repetitions
        self.mandatory = mandatory


class ArgumentParserError(Exception):
    pass


class ArgumentParser:

    def __init__(self, rules, arguments):
        self.rules = rules
        self.arguments = arguments

    def parse(self):
        args = {}
        i = 0
        arg_len = len(self.arguments)
        while i < arg_len:
            if self.arguments[i] in self.rules.with_arguments:
                try:
                    if self.arguments[i] in self.rules.with_repetitions:
                        try:
                            args[self.arguments[i]].append(self.arguments[i + 1])
                        except KeyError:
                            args[self.arguments[i]] = [(self.arguments[i + 1])]

                    else:
                        if self.arguments[i] in args:
                            raise ArgumentParserError("Option <%s> specified more than once." % self.arguments[i])
                        else:
                            args[self.arguments[i]] = self.arguments[i + 1]
                    i += 2
                    continue
                except IndexError:
                    raise ArgumentParserError("Option <%s> requires an argument."
                                              " but none specified." % self.arguments[i]) from None

            elif self.arguments[i] in self.rules.without_arguments:
                if self.arguments[i] in args:
                    raise ArgumentParserError("Option <%s> specified more than once." % self.arguments[i])
                else:
                    args[self.arguments[i]] = None

            else:
                raise ArgumentParserError("Invalid Option <%s>." % self.arguments[i])
            i += 1

        for arg in args.keys():
            try:
                options = self.rules.should_not_be_with[arg]
            except KeyError:
                pass
            else:
                if isinstance(options, str):
                    options = [options]
                for option in options:
                    if option in args:
                        raise ArgumentParserError("Option <%s> should not be used "
                                                  "along with <%s> options" % (arg, str(options)))

            try:
                options = self.rules.should_be_with[arg]
            except KeyError:
                pass
            else:
                if isinstance(options, str):
                    options = [options]
                for option in options:
                    if option not in args:
                        raise ArgumentParserError("Option <%s> should be used along "
                                                  "with <%s> options" % (arg, str(options)))

        for arg in self.rules.mandatory:
            if isinstance(arg, str):
                if arg not in args:
                    raise ArgumentParserError("Option <%s> should be specified." % arg)
            else:
                not_found = True
                for opt in arg:
                    if opt in args:
                        not_found = False
                        break
                if not_found:
                    raise ArgumentParserError("One of the options <%s> should be specified." % str(arg))
        return args


if __name__ == "__main__":
    try:
        apr = ArgumentParserRules(
            with_arguments=['-c'],
            without_arguments=['startup', 'shutdown'],
            should_not_be_with={
                'startup': ['shutdown'],
                'shutdown': ['startup']
            },
            mandatory=[('startup', 'shutdown')]
        )
        ap = ArgumentParser(apr, sys.argv[1:])
        p_args = ap.parse()
    except ArgumentParserError as e:
        print("ERROR: %s" % str(e))
        usage()
        print("ERROR: Exiting ...")
        sys.exit(1)
    except:
        print("SEVERE: Unexpected error occurred.")
        print("SEVERE: %s" % traceback.format_exc())
        sys.exit(1)
    else:
        if "startup" in p_args:
            print(Color.BOLD + '\nBlackPearl' + Color.END)
            print(startup_notes)
            print(Color.BOLD + 'Author' + Color.END)
            print(author)

            try:
                print("INFO: Initializing server configuration.")
                try:
                    config_path = p_args['-c']
                except:
                    configuration = Configuration()
                else:
                    configuration = Configuration(config=config_path)
            except Exception as e:
                print("SEVERE: %s" % str(e))
                print("SEVERE: Error occurred. Stopping the blackpearl server.")
                sys.exit(1)
            else:
                start_server(daemon=True, config=configuration)
        elif "shutdown" in p_args:
            try:
                print("INFO: Fetching server configuration.")
                try:
                    config_path = p_args['-c']
                except:
                    configuration = Configuration()
                else:
                    configuration = Configuration(config=config_path)
            except (FileNotFoundError, NameError) as e:
                print("SEVERE: %s" % str(e))
                print("SEVERE: Error occurred. Unable to stopping the blackpearl server.")
                print("SEVERE: Exiting...")
                sys.exit(1)
            else:
                stop_server(config=configuration)