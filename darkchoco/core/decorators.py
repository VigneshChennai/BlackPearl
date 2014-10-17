#!/usr/bin/python

import functools
import inspect
import threading

from darkchoco.core import urls, utils, datatype
    
def weblocation(parameter):
    '''Adds a function to web url'''

    if not isinstance(parameter, str):
        raise Exception("The decorator <weblocation> requires "\
                        "URL string as argument.")
    def parameter_wrapper(target):
        py_file_loc = inspect.getfile(target)
        
        
        if inspect.isclass(target):
            for name, method in inspect.getmembers(target(), inspect.ismethod):
                if name.startswith("__") and name.endswith("__"):
                    continue
                signature = inspect.signature(method)
                class ClassMethodInvoker:
                    def __init__(self,name):
                        self.name = name
                    def invoker(self, session, args):
                        obj = target()
                        obj.session = session
                        return getattr(obj, self.name)(**args)
                invoker = ClassMethodInvoker(name).invoker
                url = parameter + name if parameter.endswith("/") \
                        else parameter + "/" + name
                urls.add_url({
                    "url": url,
                    "handler": invoker, 
                    "signature": signature, 
                    "module_ns" : utils.get_namespace(target),
                    "module_loc" : py_file_loc, 
                    })
        
        elif inspect.isfunction(target):
            @functools.wraps(target)
            def function_wrapper(*args, **kwargs):
                # TODO : Have to do the signature validation with annotation types
                rets = target(*args, **kwargs)
                return rets
            signature = inspect.signature(target)
            def invoker(session, args):
                return function_wrapper(**args)
            #sessions not supported in function handlers
            urls.add_url({
                "url": parameter,
                "handler": invoker, 
                "signature": signature, 
                "module_ns" : utils.get_namespace(target),
                "module_loc" : py_file_loc, 
                })
            return function_wrapper
        else:
            raise Exception("Not implemented to support " + str(type(target)))

        return target
    return parameter_wrapper


def run(seconds, runtype):
    if not isinstance(seconds, int):
        raise Exception("The decorator <runevery> requires " \
                "time in seconds as parameter of type integer")
    def wrapper(target):
        if inspect.isfunction(target):
            if len(inspect.signature(target).parameters) != 0:
                raise Exception("The decorator <runevery> only "\
                        "supported for functions without parameters");   
            else:
                if runtype == "runevery":
                    def invoker_func(*args, **kwargs):
                        timer = threading.Timer(seconds, function=invoker_func)
                        timer.setDaemon(True)
                        timer.start()
                        target(*args, **kwargs)
                elif runtype == "runinterval":
                    def invoker_func(*args, **kwargs):
                        target(*args, **kwargs)
                        timer = threading.Timer(seconds, function=invoker_func)
                        timer.setDaemon(True)
                        timer.start()
                elif runtype == "runonce":
                    invoker_func = target
                else:
                    raise Exception("Unsupported runtype <%s>" % (runtype))
                timer = threading.Timer(seconds, function=invoker_func)
                timer.setDaemon(True)
                timer.start()
        else:
            raise Exception("The decorator <runevery> only "\
                        "supported for functions");
        return target
    return wrapper

def runevery(parameter):
    return run(parameter, "runevery")

def runinterval(parameter):
    return run(parameter, "runinterval")

def runonce(parameter):
    return run(parameter, "runinterval")

