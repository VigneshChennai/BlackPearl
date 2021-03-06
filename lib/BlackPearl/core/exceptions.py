#!/usr/bin/env python

# This file is part of BlackPearl.

# BlackPearl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BlackPearl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import logging

logger = logging.getLogger(__name__)


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


class UnSuccessfulException(Exception):
    """This exception should be raised when an exception has occured yet we have an output to be shared."""
    def __init__(self, status, desc, data):
        Exception.__init__(self, desc)
        self.status = status
        self.desc = desc
        self.data = data
