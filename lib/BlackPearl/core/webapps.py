#!/usr/bin/python

import traceback
import sys
import os
import importlib

from . import urls, utils
from .exceptions import RequestInvalid

deployed_apps = []
modules = {}

class Webapp:
    """This class holds all the values corresponding to a webapplication"""
    
    def __init__(self, app_location, foldername):
        self.location = app_location + "/" + foldername
        self.foldername = foldername
        self.name = None
        self.handlers = []
        self.web_modules = {}

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return "\n\tWebapp Name : %s\n" \
                "\tLocation : %s\n"\
                "\tHandler defined : %s\n"\
                "\tWeb modules : %s\n" % (
                self.name or self.foldername, 
                self.location, 
                self.handlers,
                [ url for url in self.web_modules.keys()]
                )
    
    
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
            self._init_preprocessors(config)
            self._init_posthandlers(config)
            self._init_handlers(config)
            self._init_web_modules()
        except:
            return False
            
        return True
    
    def handle_request(self, session, url, parameter):
        """This function handles the user request"""
        try:
            module = self.web_modules[url]
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
                __import__(handler)
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

    def _init_preprocessors(self,config):
        """Initializes the defined preprocessors in the webapp"""
        try:
            preprocessors = config.preprocessors
        except AttributeError:
            self.preprocessors = []
            return
        
        try:
            self.preprocessors = []
            for preprocessor in preprocessors:
                try:
                    self.preprocessors.append(__import__(preprocessor))
                except Exception as e:
                    print("SEVERE: Error in initializing "\
                        "preprocessor <%s>" % (preprocessor))   
                    print("SEVERE: See below for error occured.\n" 
                            + traceback.format_exc())
                    raise Exception("Error in initializing preprocessor")
        except TypeError:
            print("SEVERE: Preprocessors value should be a list.")
            raise Exception("Error in initializing preprocessor")

    def _init_posthandlers(self,config):
        """Initializes the defined posthandlers in the webapp"""
        try:
            posthandlers = config.posthandlers
        except AttributeError:
            self.posthandlers = []
            return
        
        try:
            self.posthandlers = []
            for posthandler in posthandlers:
                try:
                    self.posthandlers.append(__import__(posthandler))
                except Exception as e:
                    print("SEVERE: Error in initializing "\
                        "posthandler <%s>" % (posthandler))
                    print("SEVERE: See below for error occured.\n" 
                            + traceback.format_exc())
                    raise Exception("Error in initializing posthandler")
        except TypeError:
            print("SEVERE: Posthandlers value should be a list.")
            raise Exception("Error in initializing posthandler")
    
    def _init_web_modules(self):
        """Initializes the web modules in the webapp"""
        global modules
        _modules = {}
        for key, value in urls.url_map_stage.items():
            if key[1].startswith(self.location):
                if value[2] in self.handlers:
                    value.append(self)
                    if len(self.url_prefix) == 0:
                        self.web_modules[key[0]] = {
                            "func" : value[0],
                            "signature" : value[1],
                            "module_namespace" : value[2],
                            "module_location" : key[1]
                        }
                        _modules[key[0]] = self
                    else:
                        self.web_modules["/" + self.url_prefix + key[0]]  = {
                            "func" : value[0],
                            "signature" : value[1],
                            "module_namespace" : value[2],
                            "module_location" : key[1]
                        }
                        _modules["/" + self.url_prefix + key[0]] = self
                else:
                    print("WARNING: Webapp <%s> - Module<%s> not "\
                        "listed in handlers list.." \
                        " Ignoring <%s> defined in the module" % ( 
                             self.name,
                             value[2], 
                             key[0]
                             ))
        modules.update(_modules)

def initialize(location):
    """Initializes the webapplications"""
    global deployed_apps
    
    print("INFO: Adding <%s> to python path." % (location))
    sys.path.append(location)
    
    webapps_folder = [name for name in os.listdir(location)\
                         if os.path.isdir(location + os.path.sep + name)]
    print("Webapps folder: " + str(webapps_folder))
    webapps = []
    if os.environ['ENV'] == 'dev':
        try:
            webapp = Webapp(os.environ['BLACKPEARL_LIBS'], 'apis')
            if webapp.initialize():
                webapps.append(webapp)
            else:
                print("SEVERE: Ignoring the webapp")
        except:
            traceback.print_exc()
            print("Error initializing : %s" % webapp_folder)
            
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
            
    print("INFO: Webapps initialized")
    print("INFO: List of initialized webapps : %s" % (webapps))
    deployed_apps = webapps

def get_app_details_with_minimal_init(location):  
    print("INFO: Adding <%s> to python path." % (location))
    sys.path.append(location)
    
    webapps_folder = [name for name in os.listdir(location)\
                         if os.path.isdir(location + os.path.sep + name)]
    print("Webapps folder: " + str(webapps_folder))
    webapps = []
    if os.environ['ENV'] == 'dev':
        try:
            webapp = Webapp(os.environ['BLACKPEARL_LIBS'], 'apis')
            try:
                config = importlib.import_module(webapp.foldername + ".config")
            except ImportError:
                print("SEVERE: config.py not found inside webapp <apis>")
            else:
                webapp._init_basics(config)
                webapps.append(webapp)
        except:
            traceback.print_exc()
            print("Error initializing : %s" % os.environ['BLACKPEARL_LIBS'], 'apis')
    for webapp_folder in webapps_folder:
        try:
            webapp = Webapp(location, webapp_folder)
            try:
                config = importlib.import_module(webapp.foldername + ".config")
            except ImportError:
                print("SEVERE: config.py not found inside webapp <%s>" 
                        % (webapp_folder))
                continue
            webapp._init_basics(config)
            webapps.append(webapp)
        except:
            traceback.print_exc()
            print("Error initializing : %s" % webapp_folder)
    print("INFO: List of initialized webapps : %s" % (webapps))
    return webapps


