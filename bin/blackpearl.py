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
import yaml
import base64

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

__FILE_LOCATION__ = 'PORTABLE'

# Hardcoded defaults
CONFIG = {
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


def validate_and_update(loaded_config, cwd):
    category = ["path", "server", "hostname", "listen", "security", "uwsgi_options"]

    for key in loaded_config.keys():
        if key not in category:
            raise ValueError("Unknown category '<%s>' in configuration file." % key)

    path = ["lib", "share", "webapps", "run", "log", "cache"]
    try:
        path_dict = loaded_config['path']
    except KeyError:
        loaded_config['path'] = CONFIG['path'].copy()
    else:
        for key in path_dict.keys():
            if key not in path:
                raise ValueError("Unknown value '<%s>' under category <path> in configuration file." % key)

        c = CONFIG['path'].copy()
        c.update(path_dict)

        for i in ('lib', 'share', 'run', 'log', 'cache'):
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
        loaded_config['server'] = CONFIG['server'].copy()
    else:
        for key in server_dict.keys():
            if key not in server:
                raise ValueError("Unknown value '<%s>' under category <server> in configuration file." % key)

        c = CONFIG['server'].copy()
        c.update(server_dict)
        loaded_config['server'] = c

    security = ["block_size", "auto_generate_key", "key"]
    try:
        security_dict = loaded_config['security']
    except KeyError:
        loaded_config['security'] = CONFIG['security'].copy()
    else:
        for key in security_dict.keys():
            if key not in security:
                raise ValueError("Unknown value '<%s>' under category <security> in configuration file." % key)

        c = CONFIG['security'].copy()
        c.update(security_dict)
        loaded_config['security'] = c

        if c['auto_generate_key']:
            c['key'] = base64.b64encode(os.urandom(c['block_size']))
        else:
            try:
                c['key']
            except:
                raise ValueError("Key is not defined under category <security> in configuration file.") from None

    try:
        loaded_config['hostname']
    except KeyError:
        loaded_config['hostname'] = CONFIG['hostname']

    try:
        loaded_config['listen']
    except KeyError:
        loaded_config['listen'] = CONFIG['listen']

    try:
        uwsgi_option_dict = loaded_config['uwsgi_options']
    except KeyError:
        loaded_config['uwsgi_options'] = CONFIG['uwsgi_options'].copy()
    else:
        c = CONFIG['uwsgi_options'].copy()
        c.update(uwsgi_option_dict)
        loaded_config['uwsgi_options'] = c


def load(path, cwd=os.getcwd()):
    with open(path) as file:
        loaded_config = yaml.load(file)
        validate_and_update(loaded_config=loaded_config, cwd=cwd)

    return loaded_config


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

Syntax: blackpearl.py [-c <config_path>] <action>

Actions:
    1. startup
    2. shutdown
    3. newapp <appname>""")


def start_server(daemon, config):
    path = config['path']
    if os.access(path['run'], os.F_OK):
        try:
            with open(os.path.join(path['run'], "BlackPearl.pid")) as f:
                pid = f.read()
            os.kill(int(pid), 0)
            print("BlackPearl is currently running. "
                  "Shutdown it before starting it up again.\n")
            return
        except:
            pass

        shutil.rmtree(path['run'])

    os.mkdir(path['run'])
    os.mkdir(os.path.join(path['run'], 'uwsgi'))
    os.mkdir(os.path.join(path['run'], 'nginx'))
    os.mkdir(os.path.join(path['run'], 'uwsgi', 'pickle'))

    if not os.access(os.path.join(path['cache'], "virtenv"), os.F_OK):
        os.makedirs(os.path.join(path['cache'], "virtenv"))

    if not os.access(path['log'], os.F_OK):
        os.makedirs(path['log'])
    if not os.access(os.path.join(path['log'], "uwsgi"), os.F_OK):
        os.makedirs(os.path.join(path['log'], "uwsgi"))

    # open(os.path.join(os.path.join(config.run, 'uwsgi'), "worker_reload.file"), "w").close()
    print("\nStarting BlackPearl server ...")
    print("Generating log files at %s" % path['log'])
    appserver.start(config, daemon)


def stop_server(config):
    print("Stopping BlackPearl services in localhost "
          "running on <%s> user account" % pwd.getpwuid(os.getuid())[0])
    path = config['path']
    if os.access(path['run'], os.F_OK):
        print("Trying to stop BlackPearl service .", end="")
        sys.stdout.flush()
        try:
            with open(os.path.join(path['run'], "BlackPearl.pid")) as f:
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
            with_arguments=['-c', 'newapp'],
            without_arguments=['startup', 'shutdown', '-d', '--daemon'],
            should_not_be_with={
                'startup': ['shutdown'],
                'shutdown': ['startup'],
                'newapp': ['startup', 'shutdown', '-c']
            },
            mandatory=[('startup', 'shutdown', 'newapp')]
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
        try:
            print("INFO: Initializing BlackPearl Configuration.")
            try:
                config_path = p_args['-c']
            except:
                if __FILE_LOCATION__ == "PORTABLE":
                    configuration = load(os.path.join(
                        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'etc', 'config.yaml'),
                        cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
                else:
                    configuration = load('/etc/blackpearl/config.yaml')
            else:
                configuration = load(config_path)
        except Exception as e:
            print("SEVERE: %s" % str(e))
            print("SEVERE:", traceback.format_exc())
            print("SEVERE: Error occurred. Stopping the blackpearl server.")
            sys.exit(1)

        sys.path.append(configuration['path']['lib'])
        from BlackPearl.server import appserver

        if "startup" in p_args:
            print(Color.BOLD + '\nBlackPearl' + Color.END)
            print(startup_notes)
            print(Color.BOLD + 'Author' + Color.END)
            print(author)
            daemon = True if '-d' in p_args or '--daemon' in p_args else False

            start_server(daemon=daemon, config=configuration)
        elif "shutdown" in p_args:
            stop_server(config=configuration)
        elif "newapp" in p_args:
            try:
                print("INFO: Creating new webapp...")
                args_copy = p_args.copy()
                from BlackPearl.tools.newapp import invoke
                invoke(**args_copy)
            except:
                print("SEVERE: Error occurred while creating new webapp.")
                print("SEVERE:", traceback.format_exc())
