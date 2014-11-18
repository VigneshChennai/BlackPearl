#!/usr/bin/python

import sys
import inspect
import traceback

from darkchoco.core import datatype

def get_namespace(func):
    mod = inspect.getmodule(func)
    for path, module in sys.modules.items():
        if mod == module:
            return path
    raise ValueError('module not found')

def validate_parameter(signature, parameter):
    '''this function must not to be used by the webapplication'''
    parameters = signature.parameters
    p_list= []
    for p in parameters.keys():
        p_list.append(p)
    try:
        bound_arguments = signature.bind(**parameter)
    except:
        raise Exception("The received parameters <" + str(parameter)
        +"> not matching with function definition <"
        + str(p_list) +">")
    updated_args = {}
    for name, value in bound_arguments.arguments.items():
        annotation = parameters[name].annotation
        if annotation is inspect.Signature.empty:
            updated_args[name] = value
            continue
        else:
            try:
                updated_args[name] = datatype.parse(annotation, value)
            except Exception as e:
                print("WARNING: %s" % (traceback.format_exc()))
                raise Exception("Invalid data for parameter <" + name + "> : " 
                        + str(e) )
                        
    return updated_args

def parseCookie(cookieString):
    cookies = {}
    for pair in cookieString.split('; '):
        values = pair.split('=')
        cookies[values[0]] = "=".join(values[1:])
    return cookies



