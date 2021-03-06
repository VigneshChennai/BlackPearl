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

from BlackPearl.core.decorators import weblocation
from BlackPearl import application
from BlackPearl.core.exceptions import RequestInvalid, UnSuccessfulException

logger = logging.getLogger(__name__)


@weblocation('/__test_run__')
def run_testset(url, name):
    webapp = application.webapp
    try:
        module = webapp.webmodules[url]
    except KeyError:
        raise RequestInvalid("The URL <%s> not found" % url) from None

    _testset = None
    try:
        _testsets = webapp.testsets[url]
    except KeyError:
        raise RequestInvalid("No testsets found for url <%s>" % url)
    for testset in _testsets:
        if testset['name'] == name:
            _testset = testset
            break

    if _testset:
        data = _testset['func'](module['type'])
        status = data["status"]
        if status != 0:
            raise UnSuccessfulException(status=status, desc="Testcase execution failed", data=data)
        return data
    else:
        raise RequestInvalid("The name <%s> not found" % name)


@weblocation('/__test_run_all__')
def run_all_testset(url):
    webapp = application.webapp
    try:
        module = webapp.webmodules[url]
    except KeyError:
        raise RequestInvalid("The URL <%s> not found" % url) from None

    ret = []
    try:
        _testsets = webapp.testsets[url]
    except KeyError:
        raise RequestInvalid("No testsets found for url <%s>" % url)
    failed = False
    for testset in _testsets:
        data = testset['func'](module['type'])
        if data["status"] != 0:
            failed = True
        ret.append({
            "TestSet": testset['name'],
            "data": data
        })

    if failed:
        raise UnSuccessfulException(status=0, desc="Some of the testset are failed", data=ret)
    return ret


@weblocation('/__application__')
def this_app():
    app = application.webapp
    urls = []
    for url in app.webmodules.keys():
        if not url.split("/")[-1].startswith("_"):
            urls.append(url)
    urls.sort()

    preprocessors = [preprocessor['name'] for preprocessor in app.preprocessors]
    preprocessors.sort()
    posthandlers = [posthandler['name'] for posthandler in app.posthandlers]
    posthandlers.sort()
    return {
        "name": app.name,
        "url_prefix": app.url_prefix,
        "description": app.desc,
        "modules": urls,
        "preprocessors": preprocessors,
        "posthandlers": posthandlers,
        "handlers": app.handlers
    }


@weblocation('/__signature__')
def signature(url):
    """Return the signature details of the url"""
    webapp = application.webapp

    if url not in webapp.webmodules:
        raise RequestInvalid("The URL <%s> not found" % url)

    ts = []
    try:
        _testsets = webapp.testsets[url]
    except:
        pass
    else:
        for testset in _testsets:
            ts.append({
                "name": testset['name'],
                "desc": testset['desc']
            })

    return {
        "signature": webapp.webmodules[url]['arguments'],
        "type": webapp.webmodules[url]['type'],
        "desc": webapp.webmodules[url]['desc'],
        "testsets": ts
    }