#!/usr/bin/env python

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

import traceback
import sys
import os
import importlib
import inspect

from . import utils
from .exceptions import RequestInvalid

class Webapp:
    """This class holds all the values corresponding to a webapplication"""

    def __init__(self, app_location, foldername):
        self.location = app_location + "/" + foldername
        self.foldername = foldername
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
                "\tLocation : %s\n"\
                "\tHandler defined : %s\n"\
                "\tWeb modules : %s\n"\
                "\tPreprocessors : %s\n"\
                "\tPosthandlers : %s\n"\
                "\tTestsets : %s\n" % (
                self.name or self.foldername,
                self.location,
                self.handlers,
                [ url for url in self.webmodules.keys()],
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
            parameter = utils._validate_parameter(signature, parameter)
        except Exception as e:
            return {
                "status" : -201,
                "desc" : str(e)
            }
        try:
            rets = {
                "status" : 0,
                "data" : func(session, parameter),
            }
            return rets
        except RequestInvalid as ri:
            return {
                "status" : -202,
                "desc" : str(ri)
            }
        except Exception as e:
            error = traceback.format_exc()
            return {
                "status" : -203,
                "desc" : error
            }

    def initialize(self):
        """initializes the webapp"""
        try:
            config = importlib.import_module(self.foldername + ".config")
        except ImportError:
            print("SEVERE: config.py not found inside webapp <%s>"
                    % (self.foldername))
            return False

        self._init_basics(config)

        try:
            self._init_handlers(config)
        except:
            return False

        try:
            try:
                test = importlib.import_module(self.foldername + ".test")
            except ImportError as e:
                print("WARNING: Failed to initialize testcase "\
                      "in the webapp <%s>" % self.name)
                print("WARNING: Reason: %s" % str(e))
            else:
                self._init_testcases(test)
        except:
            print("ERROR: Initializing the testcases")
            print("ERROR: %s" % traceback.format_exc())
            print("WARNING: Ignoring testcases in this webapp")

        return True

    def _init_basics(self,config):
        """Basic details about the webapp is initialized using this function"""
        try:
            self.name = config.name
        except AttributeError:
            self.name = self.foldername

        try:
            desc_mod = importlib.import_module(self.foldername)
            self.desc = desc_mod.__doc__
        except AttributeError:
            self.desc = None

        try:
            self.session_enabled = config.session_enabled
            if self.session_enabled:
                try:
                    self.session_retension = config.session_retension
                except:
                    self.session_retension = None
        except AttributeError:
            self.session_enabled = False
            self.session_enabled = None

        try:
            if config.url_prefix == "ROOT":
                self.url_prefix = ""
            elif self.url_prefix == "":
                print("WARNING: Webapp<%s> - Empty url_prefix is set in the" \
                        " configuration file" % (self.name))
                self.url_prefix = self.foldername
            else:
                self.url_prefix = config.url_prefix
        except AttributeError:
            self.url_prefix = self.foldername

        try:
            self.defined_posthandlers = config.posthandlers
        except:
            pass

        try:
            self.defined_preprocessors = config.preprocessors
        except:
            pass

    def _init_handlers(self,config):
        """Initializes the defined handler in the webapp"""
        try:
            self.handlers = config.handlers
            if len(self.handlers) == 0:
                raise AttributeError("Handlers list is empty")
        except AttributeError as e:
            print("SEVERE: Webapp<%s> - configuration doesn't defined" \
                    " the list of handlers."
                    % (self.name))
            print("WARNING: See below for error occured.\n"
                    + traceback.format_exc())
            raise Exception("Error initializing handlers")

        try:
            count = 0
            for handler in self.handlers:
                print("INFO: Initializing handler <%s>" % (handler))
                module = importlib.import_module(handler)
                self._parse_module(module)
                count += 1
        except:
            print("WARNING: Webapp<%s> - Error initializing handler <%s>." \
                     "Ignoring handler .." % (self.name, handler))
            print("WARNING: See below for error occured.\n"
                    + traceback.format_exc())

        if count == 0:
            print("SEVERE: Webapp<%s> - Failed to import all the defined" \
                    " handler." % (self.name))
            raise Exception("Error initializing handlers")

    def _init_testcases(self, test):
        print("INFO: Initializing testcases")

        ismethod = inspect.ismethod
        isclass = inspect.isclass

        for name, member in inspect.getmembers(test):
            try:
                testset = member._testset
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
                    webmodule = "/" + self.url_prefix + testset['webmodule']
                    try:
                        self.testsets[webmodule].append(testset)
                    except:
                        self.testsets[webmodule] = [testset]
                    testset['webmodule'] = webmodule

                testset['func'].webmodule = webmodule


    def _parse_module(self, module):
        isfunction = inspect.isfunction
        isclass = inspect.isclass

        for name, member in inspect.getmembers(module):
            if isfunction(member):
                if hasattr(member, "_webmodule"):
                    if len(self.url_prefix) == 0:
                        url = utils.fixurl(member._webmodule['url'])
                        self.webmodules[url] = member._webmodule
                    else:
                        url = "/" + self.url_prefix + utils.fixurl(member._webmodule['url'])
                        self.webmodules[url] = member._webmodule
                elif hasattr(member, "_preprocessor"):
                    if member._preprocessor['name'] in self.defined_preprocessors:
                        self.preprocessors.append(member._preprocessor)
                    else:
                        print("WARNING: Webapp <%s> - Preprocessor<%s> not "\
                              "listed in preprocessor list.." \
                              " Ignoring preprocessor." % (self.name,
                                 member._preprocessor['name']
                                 ))
                elif hasattr(member, "_posthandler"):
                    if member._posthandler['name'] in self.defined_posthandlers:
                        self.posthandlers.append(member._posthandler)
                    else:
                        print("WARNING: Webapp <%s> - Posthandler<%s> not "\
                              "listed in posthandler list.." \
                              " Ignoring posthandler." % (self.name,
                                 member._posthandler['name']
                                 ))
            elif isclass(member) and hasattr(member, "_webmodules"):
                for webmodule in member._webmodules:
                    if len(self.url_prefix) == 0:
                        url = utils.fixurl(webmodule['url'])
                        self.webmodules[url] = webmodule
                    else:
                        url = "/" + self.url_prefix + utils.fixurl(webmodule['url'])
                        self.webmodules[url] = webmodule


def initialize(location):
    """Initializes the webapplications"""

    print("INFO: Adding <%s> to python path." % (location))
    sys.path.append(location)

    webapps_folder = [name for name in os.listdir(location)\
                         if os.path.isdir(location + os.path.sep + name)]
    print("Webapps folder: " + str(webapps_folder))
    webapps = []
    for webapp_folder in webapps_folder:
        try:
            webapp = Webapp(location, webapp_folder)
            if webapp.initialize():
                webapps.append(webapp)
            else:
                print("SEVERE: Ignoring the webapp")
        except:
            traceback.print_exc()
            print("Error initializing : %s" % webapp_folder)

    print("INFO: Webapps deployed at <%s> initialized" % location)
    print("INFO: List of initialized webapps : %s" % (webapps))
    return webapps

