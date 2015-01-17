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
#along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import functools
import inspect
import threading

from . import utils, datatype

class ClassMethodInvoker:

    def __init__(self,name, target):
        self.name = name
        self.target = target

    def __call__(self, session, args):
        obj = self.target()
        obj.session = session
        #The invoker can be called only using
        #keyword arguments
        return getattr(obj, self.name)(**args)

class FunctionInvoker:

    def __init__(self, target):
        self.target = target

    def __call__(self, session, args):
        #The invoker canbe called only using keyword arguments

        #sessions not supported in function handlers
        return self.target(**args)


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

        #Annotated Class
        if inspect.isclass(target):
            webmodules = []
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

                invoker = ClassMethodInvoker(name, target)
                if len(webname) == 0:
                    url = parameter
                else:
                    url = parameter + webname if parameter.endswith("/") \
                        else parameter + "/" + webname

                webmodules.append({
                    "url" : url,
                    "func" : invoker,
                    "handler" : method,
                    "desc" : target.__doc__
                   })
            target._webmodules = webmodules

        #Annotated function
        elif inspect.isfunction(target):

            target._webmodule = {
                "url" : parameter,
                "func" : FunctionInvoker(target),
                "handler": target,
                "desc" : target.__doc__
            }
        else:
            raise Exception("Not implemented to support " + str(type(target)))

        return target
    return parameter_wrapper

#python decorator
def preprocessor(function):
    if inspect.isfunction(function):
        signature = inspect.signature(function)
        if len(signature.parameters) != 2:
            print("WARNING: Preprocessor should have 2 argument but"\
                  " <%s> has <%s> arguments" % (
                  function.__name__ + "at" +  utils._get_module_name(function),
                  len(signature.parameters))
                  )
            print("WARNING: Ignoring the preprocessor")
            return function

        function._preprocessor = {
            "name": utils._get_module_name(function) + "." + function.__name__,
            "func": function,
            "desc": function.__doc__
        }
        return function
    else:
        print("WARNING: Not implemented to support " + str(type(target)))
        print("WARNING: Ignoring the preprocessor")
        return function

#python decorator
def posthandler(function):
    if inspect.isfunction(function):
        signature = inspect.signature(function)
        if len(signature.parameters) != 3:
            print("WARNING: Posthandler should have 3 argument but"\
                  " <%s> has <%s> arguments" % (
                  function.__name__ + "at" +  utils._get_module_name(function),
                  len(signature.parameters))
                  )
            print("WARNING: Ignoring the posthandler")
            return function

        function._posthandler = {
            "name": utils._get_module_name(function) + "." + function.__name__,
            "func": function,
            "desc": function.__doc__
        }
        return function
    else:
        print("WARNING: Not implemented to support " + str(type(target)))
        print("WARNING: Ignoring the posthandler")
        return function
        
