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
#along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import inspect

from BlackPearl.core.decorators import weblocation, webname
from BlackPearl.core import datatype
from BlackPearl import application
from BlackPearl.core.exceptions import RequestInvalid
from BlackPearl.core import datatype

@weblocation('/trial/')
class Trial:
    @webname('/dummy')
    def funny(self, name:datatype.Format("^[a-zA-Z ,.'-]+$"),
                    sex:datatype.Options("Male", "Female", "Other"),
                    age:datatype.Integer()
                ):
        return (name, sex, age)

    def __call__(self, s):
        try:
            value = self.session.name
        except:
            value = "Not set yet"
        self.session.name = s
        return "Old value : " + value

@weblocation('/applications')
def applications():
    ret = []
    for app in application.deployed_webapps:
        urls = [url for url in app.webmodules.keys()]
        preprocessors = [preprocessor['name'] for preprocessor in app.preprocessors]
        posthandlers = [posthandler['name'] for posthandler in app.posthandlers]
        ret.append({
            "name" : app.name,
            "description" : app.desc,
            "modules" : urls,
            "preprocessors": preprocessors,
            "posthandlers": posthandlers,
            "handlers" : app.handlers
        })

    return ret

@weblocation('/signature')
def signature(url):
    """Dummy entry"""
    ret = []

    try:
        webapp = application.modules[url]
    except:
        raise RequestInvalid("The URL <%s> not found" % url)

    signature = webapp.webmodules[url]['signature']
    desc = webapp.webmodules[url]['desc']


    for arg, value in signature.parameters.items():
        v = {
            "arg" : arg,
            "type" : repr(value.annotation),
            "type_def" : None,

        }

        annotation = value.annotation

        if annotation is inspect.Signature.empty:
            v['type'] = None

        if (isinstance(annotation, datatype.Format)
            or isinstance(annotation, datatype.FormatList)):
            v["type_def"] = annotation.data_format

        elif (isinstance(annotation, datatype.Options)
            or isinstance(annotation, datatype.OptionsList)):
            v["type_def"] = annotation.values

        ret.append(v)

    ts = []
    try:
        testsets = webapp.testsets[url]
    except:
        pass
    else:
        for testset in testsets:
            ts.append({
                "name" : testset['name'],
                "desc" : testset['desc']
            })


    return {"signature" : ret, "desc" : desc, "testsets" : ts}

@weblocation('/testing/testsets')
def testsets(url):
    ret = []

    try:
        webapp = application.modules[url]
    except:
        raise RequestInvalid("The URL <%s> not found" % url)

    testsets = webapp.testsets[url]
    for testset in testsets:
        ret.append({
            "name" : testset['name'],
            "desc" : testset['desc']
        })

    return ret

@weblocation('/testing/run')
def run_testset(url, name):

    try:
        webapp = application.modules[url]
    except:
        raise RequestInvalid("The URL <%s> not found" % url)

    _testset = None
    testsets = webapp.testsets[url]
    for testset in testsets:
        if testset['name'] == name:
            _testset = testset
            break

    if _testset:
        return _testset['func']()
    else:
        raise RequestInvalid("The name <%s> not found" % name)
    return ret

@weblocation("/testing/servertesting")
class Session:

    @webname("sessiontest")
    def testing(self, value):
        try:
            ret = {
                    "session" : self.session.value
            }
            self.session.value = value
        except:
            self.session.value = value
            ret = {
                   "session" : None
            }

        return ret


        
