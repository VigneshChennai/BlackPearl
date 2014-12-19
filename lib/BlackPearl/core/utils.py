#!/usr/bin/python

import sys
import inspect
import traceback

from . import datatype


def _get_module_name(func):
    """This function returns the module in which the function is defined"""
    mod = inspect.getmodule(func)
    for path, module in sys.modules.items():
        if mod == module:
            return path
    raise ValueError('module not found')

def _validate_parameter(signature, parameter):
    """This function validates the following:
    1. Checks whether the number of arguments matched.
    2. Checks the data passed is same as of annotated datatype"""
    parameters = signature.parameters
    p_list= []
    for p in parameters.keys():
        p_list.append(p)
    try:
        bound_arguments = signature.bind(**parameter)
    except:
        arguments=[p for p in parameter]
        raise Exception("The received parameters <" + str(arguments)
        +"> not matching with function definition <"
        + str(p_list) +">")
        
    #This dict will hold the final list of validated arguments
    updated_args = {}
    for name, value in bound_arguments.arguments.items():
        annotation = parameters[name].annotation
        
        #Recieved only a single value
        if not isinstance(value, list):
            if annotation is inspect.Signature.empty:
                #The value.file will None if it not a file
                if value.file:
                    updated_args[name] = {
                        "file" : value.file,
                        "filename" : value.filename,
                        "filetype" : value.type
                    }
                else:
                    #No data validation performed for non annotated arguments
                    updated_args[name] = value.value
                continue
            else:
                try:
                    #Validating the data with annotated datatype
                    updated_args[name] = datatype.parse(annotation, value)
                except Exception as e:
                    print("WARNING: %s" % (traceback.format_exc()))
                    raise Exception("Invalid data for parameter <" + name + "> : " 
                            + str(e) )
                            
        #Recieved a list of values
        else:
            #Even thought we received a list of values, the non annotated 
            #arguments will consider the first value only.
            if annotation is inspect.Signature.empty:
                value = value[0]
                #The value.file will None if it not a file
                if value.file:
                    updated_args[name] = {
                        "file" : value.file,
                        "filename" : value.filename,
                        "filetype" : value.type
                    }
                else:
                    #No data validation performed for non annotated arguments
                    updated_args[name] = value.value
                continue
            else:
                #Check the argument is annotated as List type
                if isinstance(annotation, datatype.ListType):
                    parsed_value = []
                    updated_args[name] = parsed_value
                    
                    #Validating all the received list of values
                    for v in value:
                        try:
                            parsed_value.append(datatype.parse(annotation, v))
                        except Exception as e:
                            print("WARNING: %s" % (traceback.format_exc()))
                            raise Exception("Invalid data for parameter <" + name + "> : " 
                                    + str(e) )
                                    
                #Raising exception if it is not annotated as List type
                else:
                    raise Exception("Invalid data for parameter <" + name + "> : " 
                                + "it don't support list of values" )
                        
    return updated_args



