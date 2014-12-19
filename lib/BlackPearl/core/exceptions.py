#!/usr/bin/python


class RequestInvalid(Exception):
    """This exception should be raised by a 
    handler for an invalid request"""
    pass
    
class UnAuthorizedAccess(Exception):
    """This exception should be raised by a 
    preprocessor when a request is unauthorized"""
    pass

class RequestCannotBeProcessed(Exception):
    """This exception should be raised by a 
    preprocessor when a request can't be processed due to some reason"""
    pass
