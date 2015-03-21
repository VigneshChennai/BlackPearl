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

import traceback
import sys
import inspect
import os
import importlib
import yaml

from . import utils
from .exceptions import RequestInvalid


class Webapp:
    """This class holds all the values corresponding to a web application"""

    def __init__(self, app_location, folder_name):
        self.id = ""
        self.location = os.path.join(app_location, folder_name)
        self.folder_name = folder_name
        self.name = None
        self.handlers = []
        self.webmodules = {}
        self.testsets = {}
        self.preprocessors = []
        self.posthandlers = []

        self.defined_preprocessors = []
        self.defined_posthandlers = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "\n\tWebapp Name : %s\n" \
               "\tLocation : %s\n" \
               "\tHandler defined : %s\n" \
               "\tWeb modules : %s\n" \
               "\tPreprocessors : %s\n" \
               "\tPosthandlers : %s\n" \
               "\tTestsets : %s\n" % (
                   self.name or self.folder_name,
                   self.location,
                   self.handlers,
                   [url for url in self.webmodules.keys()],
                   self.preprocessors,
                   self.posthandlers,
                   ["For webmodule: " + key + " " + str([testset['name'] for testset in testsets])
                    for key, testsets in self.testsets.items()]
               )

    def handle_request(self, session, url, parameter):
        """This function handles the user request"""
        try:
            module = self.webmodules[url]
            func = module['func']
            signature = module['signature']
        except:
            raise ValueError("Invalid url : " + url)

        try:
            parameter = utils.validate_parameter(signature, parameter)
        except Exception as e:
            return {
                "status": -201,
                "desc": str(e)
            }
        try:
            ret = {
                "status": 0,
                "data": func(session, parameter),
            }
            return ret
        except RequestInvalid as ri:
            return {
                "status": -202,
                "desc": str(ri)
            }
        except Exception:
            error = traceback.format_exc()
            return {
                "status": -203,
                "desc": error
            }

    def initialize(self):
        """initializes the webapp"""

        print("INFO: Initializing webapp folder <%s>" % self.folder_name)
        try:
            with open(os.path.join(self.location, "config.yaml")) as config_file:
                loaded_config = yaml.load(config_file)

            class Config:
                pass

            config = Config()
            for key, value in loaded_config.items():
                setattr(config, key, value)

        except yaml.parser.ParserError:
            print("SEVERE: config.yaml contains errors")
            print("SEVERE: Actual error: ", traceback.format_exc())
            return False
        except:
            print("SEVERE: config.yaml not found inside webapp <%s> or error loading it" % self.folder_name)
            print("SEVERE: Actual error: ", traceback.format_exc())
            return False

        self._init_basics(config)

        try:
            self._init_handlers(config)
        except:
            print("SEVERE: ", traceback.format_exc())
            return False

        try:
            test_sets = [testset[:-3] for testset in os.listdir(os.path.join(self.location, "test"))
                         if testset.endswith(".py")]

            if len(test_sets) == 0:
                print("INFO: No testsets defined.")
            for test_set in test_sets:
                try:
                    print("INFO: Initializing test sets in <", test_set, ">", sep="")
                    test = importlib.import_module(test_set)
                except ImportError as e:
                    print("WARNING: Failed to initialize testcase in the webapp", self.name)
                    print("WARNING: Reason:", str(e))
                else:
                    self._init_testcases(test)
        except:
            print("ERROR: Initializing the testcases")
            print("ERROR: %s" % traceback.format_exc())
            print("WARNING: Ignoring testcases in this webapp")

        print("INFO: Initialization of webapp <%s> completed." % self.name)
        return True

    def _init_basics(self, config):
        """Basic details about the webapp is initialized using this function"""
        try:
            if not config.enabled:
                raise NotEnabledError("Webapp is configured as disabled")
            else:
                self.enabled = True
        except AttributeError:
            self.enabled = True
        try:
            self.name = config.name
        except AttributeError:
            self.name = self.folder_name

        try:
            self.desc = config.desc
        except AttributeError:
            self.desc = None

        try:
            self.session_enabled = config.session_enabled
            if self.session_enabled:
                try:
                    self.session_retention = config.session_retention
                except:
                    self.session_retention = None
        except AttributeError:
            self.session_enabled = False
            self.session_enabled = None

        try:
            if len(self.url_prefix) == 0:
                print("WARNING: Webapp<%s> - Empty url_prefix is set in the"
                      " configuration file" % self.name)
                print("WARNING: Using folder name </%s> as url_prefix for this webapp." % self.folder_name)
                self.url_prefix = self.folder_name
            else:
                if self.url_prefix.startswith('/'):
                    self.url_prefix = config.url_prefix
                else:
                    print("WARNING: url_prefix is not defined with '/' in the "
                          "beginning. but defined as <%s>" % self.url_prefix)
                    print("WARNING: Adding '/' in front in URL prefix.")
                    self.url_prefix = '/' + config.url_prefix

        except AttributeError:
            self.url_prefix = "/" + self.folder_name

        self.id = self.url_prefix[1:].replace("/","_")

        print("INFO: URL prefix <%s>" % self.url_prefix)

        try:
            self.defined_posthandlers = config.posthandlers
        except:
            pass

        try:
            self.defined_preprocessors = config.preprocessors
        except:
            pass

    def _init_handlers(self, config):
        """Initializes the defined handler in the webapp"""
        try:
            self.handlers = config.handlers
            if len(self.handlers) == 0:
                raise AttributeError("Handlers list is empty")
        except AttributeError:
            print("SEVERE: Webapp<%s> - configuration doesn't defined"
                  " the list of handlers." % self.name)
            print("WARNING: See below for error occurred.\n"
                  + traceback.format_exc())
            raise Exception("Error initializing handlers")

        count = 0
        self.handlers.insert(0, "BlackPearl.core.handlers")
        for handler in self.handlers:
            try:
                print("INFO: Initializing handler <%s>" % handler)
                module = importlib.import_module(handler)
                self._parse_module(module)
                count += 1
            except:
                print("WARNING: Webapp<%s> - Error initializing handler <%s>."
                      "Ignoring handler .." % (self.name, handler))
                print("WARNING: See below for error occurred.\n"
                      + traceback.format_exc())

        if count == 0:
            print("SEVERE: Webapp<%s> - Failed to import all the defined"
                  " handler." % self.name)
            raise Exception("Error initializing handlers")

    def _init_testcases(self, test):
        print("INFO: Initializing testcases")

        for name, member in inspect.getmembers(test):
            try:
                testset = member.__testset__
            except:
                pass
            else:
                if len(self.url_prefix) == 0:
                    webmodule = testset['webmodule']
                    try:
                        self.testsets[webmodule].append(testset)
                    except:
                        self.testsets[webmodule] = [testset]
                else:
                    webmodule = self.url_prefix + testset['webmodule']
                    try:
                        self.testsets[webmodule].append(testset)
                    except:
                        self.testsets[webmodule] = [testset]
                    testset['webmodule'] = webmodule

                testset['func'].webmodule = webmodule

    def _check_url(self, url, name, member):
        if url in self.webmodules:
            print("WARNING: Url<%s> is already defined. "
                  "Ignoring webmodule<%s> defined in <%s>" % (url, name, inspect.getmodule(member).__file__))
            return False
        return True

    def _parse_module(self, module):
        isfunction = inspect.isfunction
        isclass = inspect.isclass

        for name, member in inspect.getmembers(module):
            if isfunction(member):
                if hasattr(member, "__webmodule__"):
                    if len(self.url_prefix) == 0:
                        url = utils.fixurl(member.__webmodule__['url'])
                        if self._check_url(url, name, member):
                            self.webmodules[url] = member.__webmodule__
                    else:
                        url = self.url_prefix + utils.fixurl(member.__webmodule__['url'])
                        if self._check_url(url, name, member):
                            self.webmodules[url] = member.__webmodule__
                elif hasattr(member, "__preprocessor__"):
                    if member.__preprocessor__['name'] in self.defined_preprocessors:
                        self.preprocessors.append(member.__preprocessor__)
                    else:
                        print("WARNING: Webapp <%s> - Preprocessor<%s> not "
                              "listed in preprocessor list.."
                              " Ignoring preprocessor."
                              % (self.name, member.__preprocessor__['name']))
                elif hasattr(member, "__posthandler__"):
                    if member.__posthandler__['name'] in self.defined_posthandlers:
                        self.posthandlers.append(member.__posthandler__)
                    else:
                        print("WARNING: Webapp <%s> - Posthandler<%s> not "
                              "listed in posthandler list.."
                              " Ignoring posthandler."
                              % (self.name, member.__posthandler__['name']))
            elif isclass(member) and hasattr(member, "__webmodules__"):
                for webmodule in member.__webmodules__:
                    if len(self.url_prefix) == 0:
                        url = utils.fixurl(webmodule['url'])
                        if self._check_url(url, name, member):
                            self.webmodules[url] = webmodule
                    else:
                        url = self.url_prefix + utils.fixurl(webmodule['url'])
                        if self._check_url(url, name, member):
                            self.webmodules[url] = webmodule


class NotEnabledError(Exception):
    pass


def get_webapp_folders(location):
    if not os.access(location, os.F_OK):
        print("WARNING: Webapps folder<%s> not found. Ignoring.. " % location)
    return [name for name in os.listdir(location) if os.path.isdir(location + os.path.sep + name)]


def analyze(location, webapp_folder):
    """Initializes the web applications"""
    if not os.access(location, os.F_OK):
        print("WARNING: Webapps folder<%s> not found. Ignoring.. " % location)
        return

    for l in (os.path.join(location, webapp_folder, "src"),
              os.path.join(location, webapp_folder, "lib"),
              os.path.join(location, webapp_folder, 'test')):
        print("INFO: Adding <%s> to python path." % l)
        sys.path.append(l)

    try:
        webapp = Webapp(location, webapp_folder)
        if webapp.initialize():
            return webapp
        else:
            print("SEVERE: Ignoring the webapp")
    except NotEnabledError:
        print("INFO: Ignoring <%s> as is it disabled in configuration file")
    except:
        traceback.print_exc()
        print("Error initializing : %s" % webapp_folder)