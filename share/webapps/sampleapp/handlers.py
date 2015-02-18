
#!/bin/env python

from BlackPearl.core import datatype
from BlackPearl.core.decorators import weblocation


@weblocation("helloworld")
def helloworld():
    ret = {
            "msg" : "Hello world",
            "desc" : "My first hello world BlackPearl web application"
    }
    return ret


@weblocation("/calculator")
def simple_calculator(operation: datatype.Options("add", "sub", "mul", "div"),
                      value1: datatype.Float(),
                      value2: datatype.Float()):
    if operation == "add":
        return value1 + value2
    elif operation == "sub":
        return value1 - value2
    elif operation == "mul":
        return value1 * value2
    else:
        return value1 / value2
