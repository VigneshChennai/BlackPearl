#!/usr/bin/python

import traceback
import sys
import os
import importlib

from darkchoco.core import urls, utils

class Webapp:
    def __init__(self, app_location, foldername):
        self.location = app_location + "/" + foldername
        self.foldername = foldername
        self.name = None
        self.handlers = []

    def initilize(self):
        try:
            config = importlib.import_module(self.foldername + ".config")
        except ImportError:
            print("SEVERE: config.py not found inside webapp <%s>" 
                    % (seld.foldername))
            return False

        self.__init_basics__(config)
        
        try:
            self.__init_preprocessors__(config)
            self.__init_posthandlers__(config)
            self.__init_handlers__(config)
        except:
            return False
            
        return True
    
    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return "\n\tWebapp Name : %s\n" \
                "\tLocation : %s\n"\
                "\tHandler defined : %s\n" % (
                self.name or self.foldername, 
                self.location, 
                self.handlers
                )

    def __init_basics__(self,config):
        try:
            self.name = config.name
        except AttributeError:
            self.name = self.foldername

        try:
            self.desc = config.desc
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
            
    def __init_preprocessors__(self,config):
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

    def __init_posthandlers__(self,config):
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


    def __init_handlers__(self,config):
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
            
    def handle_request(self, session, url, parameter):
        return __invoke_web_func__(session, url, parameter)
        


def get_app_details(location):
    print("INFO: Adding <%s> to python path." % (location))
    sys.path.append(location)
    
    webapps_folder = [name for name in os.listdir(location)\
                         if os.path.isdir(location + os.path.sep + name)]
    print("Webapps folder: " + str(webapps_folder))
    webapps = []
    for webapp_folder in webapps_folder:
        try:
            webapp = Webapp(location, webapp_folder)
            if webapp.initilize():
                webapps.append(webapp)
            else:
                print("SEVERE: Ignoring the webapp")
        except:
            traceback.print_exc()
            print("Error initializing : %s" % webapp_folder)
            
    print("INFO: Webapps initialized")
    print("INFO: List of initialized webapps : %s" % (webapps))
    return webapps

def get_app_details_with_minimal_init(location):
    print("INFO: Adding <%s> to python path." % (location))
    sys.path.append(location)
    
    webapps_folder = [name for name in os.listdir(location)\
                         if os.path.isdir(location + os.path.sep + name)]
    print("Webapps folder: " + str(webapps_folder))
    webapps = []
    for webapp_folder in webapps_folder:
        try:
            webapp = Webapp(location, webapp_folder)
            try:
                config = importlib.import_module(webapp.foldername + ".config")
            except ImportError:
                print("SEVERE: config.py not found inside webapp <%s>" 
                        % (seld.foldername))
                continue
            webapp.__init_basics__(config)
            webapps.append(webapp)
        except:
            traceback.print_exc()
            print("Error initializing : %s" % webapp_folder)
    print("INFO: List of initialized webapps : %s" % (webapps))
    return webapps


def get_webapp(url):
    try:
        invoke_details = urls.url_map[url]
    except:
        raise ValueError("Requested URL not found : %s" % (url))
    if invoke_details:
        return urls.url_map[url][3]
    else:
        return None

def __invoke_web_func__(session, url, parameter):
    '''this function must not to be used by the webapplication'''
    # TODO : Need to handle invalid url
    try:
        func, signature, module_ns, webapp = urls.url_map[url]
    except:
        raise ValueError("Invalid url : " + url)
    
    try:
        parameter = utils.validate_parameter(signature, parameter)
    except Exception as e:
        return {
            "status" : -1,
            "desc" : str(e)
        }
    try:
        rets = {
            "status" : 0,
            "data" : func(session, parameter),
        }
        return rets
    except Exception as e:
        error = traceback.format_exc()
        return {
            "status" : -2,
            "desc" : error
        }

