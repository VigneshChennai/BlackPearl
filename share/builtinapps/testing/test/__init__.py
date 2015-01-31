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


@testset(name="Session Max - Min value check", webmodule="/servertesting/sessiontest")
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


@testset(name="Session value check", webmodule="/servertesting/sessiontest")
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


@testset(name="Integer parameter test - correct values", webmodule="/servertesting/integerparamtest")
def testing1():
    for i in range(0, 1000):
        result = testcase({
            "value": str(i)
        })
        test(result['status'], 0)


@testset(name="Integer parameter test - Incorrect values", webmodule="/servertesting/integerparamtest")
def testing2():
    print("Testing: String value to integer")
    for i in range(0, 1000):
        result = testcase({
            "value": str(i) + "sd"
        })
        test(result['status'], -201)
    print("'String value to integer' test completed successfully")
    print("Testing: Floating value to Integer")
    for i in range(0, 1000):
        result = testcase({
            "value": str(i) + ".01"
        })
        test(result['status'], -201)

    print("'Floating value to Integer' test completed successfully")


@testset(name="Float parameter test - correct values", webmodule="/servertesting/floatparamtest")
def testing3():
    print("Testing with integer values")
    for i in range(0, 1000):
        result = testcase({
            "value": str(i)
        })
        test(result['status'], 0)

    print("Testing with float values")
    for i in range(0, 1000):
        result = testcase({
            "value": str(i) + ".34"
        })
        test(result['status'], 0)


@testset(name="Float parameter test - Incorrect values", webmodule="/servertesting/floatparamtest")
def testing4():
    print("Testing: String value to Float")
    for i in range(0, 1000):
        result = testcase({
            "value": str(i) + "sd"
        })
        test(result['status'], -201)
    print("'String value to float' test completed successfully")


@testset(name="Option parameter test - correct values", webmodule="/servertesting/optionparamtest")
def testing5():
    result = testcase({
        "value": "Male"
    })
    test(result['status'], 0)

    result = testcase({
        "value": "Female"
    })
    test(result['status'], 0)


@testset(name="Option parameter test - Incorrect values", webmodule="/servertesting/optionparamtest")
def testing6():
    result = testcase({
        "value": "male"
    })
    test(result['status'], -201)

    result = testcase({
        "value": "female"
    })
    test(result['status'], -201)


@testset(name="Format parameter test - correct values", webmodule="/servertesting/formatparamtest")
def testing7():
    result = testcase({
        "value": "Vigneshwaran P"
    })
    test(result['status'], 0)

    result = testcase({
        "value": "Iron Man"
    })
    test(result['status'], 0)


@testset(name="Format parameter test - Incorrect values", webmodule="/servertesting/formatparamtest")
def testing8():
    result = testcase({
        "value": "Iron Man 3"
    })
    test(result['status'], -201)

    result = testcase({
        "value": "007"
    })
    test(result['status'], -201)


@testset(name="Integer list parameter test - correct values", webmodule="/servertesting/integerlistparamtest")
def testing_list1():
    for i in range(0, 1000):
        result = testcase({
            "value": [i, i + 12]
        })
        test(result['status'], 0)
        print("Data : %s" % result['data'])


@testset(name="Integer list parameter test - Incorrect values", webmodule="/servertesting/integerlistparamtest")
def testing_list2():
    print("Testing: String value to integer")
    for i in range(0, 1000):
        result = testcase({
            "value": [str(i) + "sd", i]
        })
        test(result['status'], -201)
    print("'String value to integer' test completed successfully")
    print("Testing: Floating value to Integer")
    for i in range(0, 1000):
        result = testcase({
            "value": [str(i) + ".01", i]
        })
        test(result['status'], -201)

    print("'Floating value to Integer' test completed successfully")


@testset(name="Float list parameter test - correct values", webmodule="/servertesting/floatlistparamtest")
def testing_list3():
    print("Testing with integer values")
    for i in range(0, 1000):
        result = testcase({
            "value": [i, i+1]
        })
        test(result['status'], 0)

    print("Testing with float values")
    for i in range(0, 1000):
        result = testcase({
            "value": [str(i) + ".34", i]
        })
        test(result['status'], 0)


@testset(name="Float list parameter test - Incorrect values", webmodule="/servertesting/floatlistparamtest")
def testing_list4():
    print("Testing: String value to Float")
    for i in range(0, 1000):
        result = testcase({
            "value": [str(i) + "sd", "sdf"]
        })
        test(result['status'], -201)
    print("'String value to float' test completed successfully")


@testset(name="Option list parameter test - correct values", webmodule="/servertesting/optionlistparamtest")
def testing_list5():
    result = testcase({
        "value": ["Male", "Female"]
    })
    test(result['status'], 0)

    result = testcase({
        "value": ["Female", "Male"]
    })
    test(result['status'], 0)


@testset(name="Option list parameter test - Incorrect values", webmodule="/servertesting/optionlistparamtest")
def testing_list6():
    result = testcase({
        "value": ["male", "Male"]
    })
    test(result['status'], -201)

    result = testcase({
        "value": ["female", "male"]
    })
    test(result['status'], -201)


@testset(name="Format list parameter test - correct values", webmodule="/servertesting/formatlistparamtest")
def testing_list7():
    result = testcase({
        "value": ["Vigneshwaran P", "P Vigneshwaran"]
    })
    test(result['status'], 0)

    result = testcase({
        "value": ["Iron Man", "Man Iron"]
    })
    test(result['status'], 0)


@testset(name="Format list parameter test - Incorrect values", webmodule="/servertesting/formatlistparamtest")
def testing_list8():
    result = testcase({
        "value": ["Iron Man 3", "Iron Man 4"]
    })
    test(result['status'], -201)

    result = testcase({
        "value": ["007", "234"]
    })
    test(result['status'], -201)