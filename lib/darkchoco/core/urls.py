#!/usr/bin/python

from darkchoco.core import utils

url_map = {}
url_map_stage = {}

def ammend_urls_with_webapp_info(webapp):
    for key, value in url_map_stage.items():
        if key[1].startswith(webapp.location):
            if value[2] in webapp.handlers:
                value.append(webapp)
                if len(webapp.url_prefix) == 0:
                    url_map[key[0]] = value
                else:
                    url_map["/" + webapp.url_prefix + key[0]] = value
            else:
                print("WARNING: Webapp <%s> - Module<%s> not "\
                    "listed in handlers list.." \
                    " Ignoring <%s> defined in the module" % ( 
                         webapp.name,
                         value[2], 
                         key[0]
                         ))

def initialize(webapps):
    global url_map_stage
    for webapp in webapps:
        ammend_urls_with_webapp_info(webapp)

    print("INFO: List of URLS initialized.")
    for url, value in url_map.items():
        print("INFO : URL <%s> from module <%s>" % (url, value[2]))
    del url_map_stage
        
def add_url(details):
    '''this function must not to be used by the webapplication'''
    url = details["url"]
    func = details["handler"]
    signature = details["signature"]
    module_ns = details["module_ns"]
    module_loc = details["module_loc"]
    url_map_stage[(url, module_loc)] = [func, signature, module_ns]
