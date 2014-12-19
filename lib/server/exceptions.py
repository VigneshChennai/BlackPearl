#!/usr/bin/python

class NotSupported(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        
class NotImpletementYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class NotStartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class NotRestartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        
class InvalidState(Exception):
    def __init__(self, msg):
        super().__init__(msg)
