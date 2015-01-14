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
#along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

from BlackPearl.testing import testset, testcase, test

@testset(name="Application API testing", webmodule="/applications")
def smoketest():
    result = testcase({})
    test(result['status'], 0)

@testset(name="Application API testin2g", webmodule="/applications")
def smoketest1():
    result = testcase({})
    test(result['status'], 0)


@testset(name="session_testing", webmodule="/trial")
def session_testing():
    print("Checking first iteration")
    result = testcase({'s' : "older"})
    test(result['data'], 'Old value : Not set yet')

    print("Checking second iteration")
    result = testcase({'s' : "older1"})
    test(result['data'], 'Old value : older')

    print("Checking Third iteration")
    result = testcase({'s' : "older2"})
    test(result['data'], 'Old value : older1')

    print("All testcase completed successfully")




