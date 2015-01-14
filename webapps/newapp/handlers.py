#!/bin/env python

from BlackPearl.core.decorators import weblocation

@weblocation("hello")
def hello():
    ret = {
            "msg" : "Hello world",
            "desc" : "My first helloworld BlackPearl web application"
    }
    return ret

