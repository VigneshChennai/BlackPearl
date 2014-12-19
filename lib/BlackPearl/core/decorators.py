#!/usr/bin/python

import functools
import inspect
import threading

from . import urls, utils, datatype

#Python decorator
def webname(parameter):
    """Exposes a method to web."""
    
    if not isinstance(parameter, str):
        raise Exception("The decorator <webname> requires "\
                        "string as argument.")
    def append_name(target):
        target._webname = parameter
        return target
    
    return append_name
    
#Python decorator
def weblocation(parameter):
    '''Exposes a method a function or a class to web'''

    if not isinstance(parameter, str):
        raise Exception("The decorator <weblocation> requires "\
                        "URL string as argument.")
    def parameter_wrapper(target):
        py_file_loc = inspect.getfile(target)
        
        #Annotated Class 
        if inspect.isclass(target):
            
            for name, method in inspect.getmembers(target(), inspect.ismethod):
                #Checking whether the method is expossed to called from 
                #web in the Class
                try:
                    webname = method._webname
                except:
                    if name == '__call__':
                        webname = ""
                    else:
                        continue
                
                class ClassMethodInvoker:
                    def __init__(self,name):
                        self.name = name
                    def invoker(self, session, args):
                        obj = target()
                        obj.session = session
                        #The invoker can be called only using 
                        #keyword arguments
                        return getattr(obj, self.name)(**args)
                invoker = ClassMethodInvoker(name).invoker

                if len(webname) == 0:
                    url = parameter
                else:
                    url = parameter + webname if parameter.endswith("/") \
                        else parameter + "/" + webname
                signature = inspect.signature(method)
                urls.add_url({
                    "url": url,
                    "handler": invoker, 
                    "signature": signature, 
                    "module_ns" : utils._get_module_name(target),
                    "module_loc" : py_file_loc, 
                    })
                    
        #Annotated function
        elif inspect.isfunction(target):
            signature = inspect.signature(target)
            def invoker(session, args):
                #The invoker canbe called only using keyword arguments
                
                #sessions not supported in function handlers
                return target(**args)

            urls.add_url({
                "url": parameter,
                "handler": invoker, 
                "signature": signature, 
                "module_ns" : utils._get_module_name(target),
                "module_loc" : py_file_loc, 
                })
        else:
            raise Exception("Not implemented to support " + str(type(target)))

        return target
    return parameter_wrapper

