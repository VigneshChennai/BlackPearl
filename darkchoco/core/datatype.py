#!/usr/bin/python

import re


def isvalid(dataType, data):
    try:
        return dataType.__is_valid__(data)
    except AttributeError as ae:
        raise Exception("DataType <"+ str(dataType.__class__.__name__) 
            + "> is a invalid to be used in web "
            + "method annotations.\nActual error: " + str(ae))

def parse(dataType, data):
    if isvalid(dataType, data):
        return dataType.__parse__(data)
    else:
        raise Exception("%s, but <%s> is given." % (str(dataType), str(data)))
    
class Type:
    def __is_valid__(self, data):
        return True
    def __parse__(self, data):
        return data;

class Float(Type):
    def __is_valid__(self, data):
        try:
            float(data[0])
            return True
        except:
            return False
    def __parse__(self, data):
        return float(data[0])
    
    def __repr__(self):
        return "Float datatype"
    def __str__(self):
        return "It accepts floating point number. Example : 234.123"

class Integer(Type):
    def __is_valid__(self, data):
        try:
            int(data[0])
            return True
        except:
            return False
    def __parse__(self, data):
        return int(data[0])
    def __repr__(self):
        return "Integer datatype"
    def __str__(self):
        return "It accepts only non floating point number. Example : 234"
    
class Format(Type):
    """Custom regex based format"""
    def __init__(self, data_format):
        self.pattern = re.compile(data_format)
        
    def __is_valid__(self, data):
        try:
            if self.pattern.match(data[0]):
                return True
            else:
                return False
        except:
            return False

    def __parse__(self, data):
        return data[0]
        
    def __repr__(self):
        return "Custom regex based format"
    
    def __str__(self):
        return "It is defined to accept only value of " \
                       "format <%s> as value" % (str(self.pattern))

class Options(Type):
    def __init__(self, *values):
        v = []
        for value in values:
            v.append(str(value))
        self.values = v
    def __is_valid__(self, data):
        try:
            if data[0] in self.values:
                return True
            else:
                return False
        except:
            return False
    def __parse__(self, data):
        return data[0]

    def __repr__(self):
        return "Option datatype"
        
    def __str__(self):
        return "It is defined to accept only one of the <%s> as value" % (str(self.values))
       
