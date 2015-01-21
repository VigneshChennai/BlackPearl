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

from BlackPearl.testing import testset, testcase, test


@testset(name="Session Max - Min value check",
         webmodule="/testing/servertesting/sessiontest")
def session_max_min_check():
    for i in range(1, 4001):
        val = "x" * i
        print("Checking with session size <%s>" % i)
        result = testcase({"value": val})
        try:
            test(result['status'], 0)
        except:
            print("Working session size is <%s>" % (i-1))
            return

    print("All testcase completed successfully")


@testset(name="Session value check", webmodule="/testing/servertesting/sessiontest")
def session_value_check():
    old_value = None
    for i in range(1, 4000):
        val = "x" * i
        print("Checking with session size <%s>" % i)
        result = testcase({"value": val})
        try:
            test(result['data']['session'], old_value)
        except:
            print(result)
            return
        old_value = val

    print("All testcase completed successfully")