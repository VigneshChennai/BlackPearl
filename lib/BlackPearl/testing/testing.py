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


import json
import inspect
import traceback
from time import strftime
import urllib.request
import urllib.parse


__all__ = ['testset', 'testcase', 'test', 'TestcaseFailed',
           'InvalidTestcaseInvoke', 'ErrorInvokingWebModule',
           'TestcaseFailed', 'TestcaseError']

listen = "localhost:8080"


class TestsetInvoker:
    def __init__(self, name, webmodule, function):
        self.function = function
        self.name = name
        self.webmodule = webmodule

    def __call__(self):
        # The below three variable will used for inspection from testcase
        caller = self.__call__
        webmodule = self.webmodule
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor())

        testset_outs = ['[%s] %s' % (strftime("%Y-%m-%d %H:%M:%S"), "Invoking the Testset<%s>" % self.name)]

        try:
            self.function()
        except TestcaseFailed as e:
            testset_outs.append('[%s] %s' % (strftime("%Y-%m-%d %H:%M:%S"),
                                             "Testset<%s> execution failed." % self.name))
            return {
                "status": -1,
                "result": "Failed",
                "desc": str(e),
                "prints": testset_outs
            }
        except TestcaseError as e:
            print("ERROR: %s" % traceback.format_exc())
            testset_outs.append('[%s] %s' % (strftime("%Y-%m-%d %H:%M:%S"),
                                             "Testset<%s> terminated due to an internal"
                                             " error." % self.name))
            return {
                "status": -3,
                "result": "ServerIssue",
                "desc": "Error occurred in invoking the testcase. "
                        "Error: %s. Check the server log for"
                        " more details." % str(e),
                "prints": testset_outs
            }
        except Exception as e:
            return {
                "status": -2,
                "result": "Error",
                "desc": "Error occurred in invoking the Testcase<%s>. "
                        "Error: (%s) at line <%s>" % (self.name,
                                                      type(e).__name__ + ": " + str(e),
                                                      traceback.extract_tb(e.__traceback__)[-1][1]),
                "prints": testset_outs
            }
        else:
            testset_outs.append('[%s] %s' % (strftime("%Y-%m-%d %H:%M:%S"),
                                             "Testset<%s> successfully completed" % self.name))
            return {
                "status": 0,
                "result": "Success",
                "prints": testset_outs
            }


# python decorator
def testset(name, webmodule):
    """It's a decorator which to be used for defining the testsets."""

    def alt_func(func):
        module = inspect.getmodule(func)
        if not hasattr(module, 'print'):
            module.print = testprint

        # correcting the webmodule url if not properly written.
        url_seg = []
        for segment in webmodule.split('/'):
            segment = segment.strip()
            if len(segment) != 0:
                url_seg.append(segment)
        _webmodule = "/" + "/".join(url_seg)

        invoker = TestsetInvoker(name, webmodule, func)

        func.__testset__ = {
            "name": name,
            "desc": func.__doc__,
            "webmodule": _webmodule,
            "func": invoker,
        }

        return func

    return alt_func


def testcase(testcase_input):
    """testcase(input) function must be used within a testset.

input - should be a dict object containing the input values for webmodule"""

    try:

        prev_frame = inspect.currentframe().f_back.f_back

        # getting the function object from locals
        # func = prev_frame.f_locals['caller']
        webmodule = prev_frame.f_locals['webmodule']
        # getting the opener object for this current testcase run.
        opener = prev_frame.f_locals['opener']
    except:
        raise InvalidTestcaseInvoke("The testcase function must be invoked "
                                    "from a function decorated with"
                                    " @testset") from None
    else:
        try:
            # invoking the webmodule
            rets = _invoke_webmodule(opener, webmodule, testcase_input)
            return json.loads(rets.decode())
        except:
            # in case any error occurred during invoking of webmodule
            raise TestcaseError("Error: %s" % traceback.format_exc())


def test(first, second):
    """compares the first and second values.
    If not equals, raises TestcaseFailed Exception"""
    # basic comparison
    if first != second:
        raise TestcaseFailed("Test failed: Excepted value "
                             ": <%s> Return value : <%s>" % (second, first))


def _invoke_webmodule(opener, url, testcase_input):
    """Internal function which invokes the webmodule"""
    # quote function will be used to quote the values passed as
    # param to the webmodule

    t_inputs = []
    for key, value in testcase_input.items():
        if isinstance(value, str):
            t_inputs.append((key, value))
        else:
            try:
                for v in value:
                    t_inputs.append((key, v))
            except:
                t_inputs.append((key, value))

    # invoking the webmodule.
    # TODO: https protocol need to be supported.
    # TODO: Support file and post form submit method.
    response = opener.open("http://" + listen + url,
                           urllib.parse.urlencode(t_inputs).encode('UTF-8'))
    return response.read()


def testprint(*args, **kwargs):
    try:
        prev_frame = inspect.currentframe().f_back.f_back

        prints = prev_frame.f_locals['testset_outs']
    except:
        print(*args, **kwargs)
    else:
        args1 = [str(arg) for arg in args]
        if 'file' not in kwargs:
            try:
                msg = kwargs['sep'].join(args1)
            except:
                msg = ''.join(args1)
            prints.append('[' + strftime("%Y-%m-%d %H:%M:%S") + '] ' + msg)
        else:
            print(*args, **kwargs)


class TestcaseFailed(Exception):
    pass


class InvalidTestcaseInvoke(Exception):
    pass


class ErrorInvokingWebModule(Exception):
    pass


class TestcaseError(Exception):
    pass
