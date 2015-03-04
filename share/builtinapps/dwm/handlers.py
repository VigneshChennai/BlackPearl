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

import inspect

from BlackPearl.core.decorators import weblocation
from BlackPearl import application
from BlackPearl.core.exceptions import RequestInvalid


@weblocation('/applications')
def applications():
    ret = []
    for app in application.deployed_webapps:
        urls = []
        for url in app.webmodules.keys():
            if not url.split("/")[-1].startswith("_"):
                urls.append(url)
        urls.sort()

        preprocessors = [preprocessor['name'] for preprocessor in app.preprocessors]
        preprocessors.sort(key=lambda prep: prep['name'])
        posthandlers = [posthandler['name'] for posthandler in app.posthandlers]
        posthandlers.sort(key=lambda post: post['name'])
        ret.append({
            "name": app.name,
            "url_prefix": app.url_prefix,
            "description": app.desc,
            "modules": urls,
            "preprocessors": preprocessors,
            "posthandlers": posthandlers,
            "handlers": app.handlers
        })
        ret = sorted(ret, key=lambda data: data['name'])
    return ret


@weblocation('/signature')
def signature(url):
    """Return the signature details of the url"""
    ret = []

    try:
        webapp = application.modules[url]
    except:
        raise RequestInvalid("The URL <%s> not found" % url)

    desc = webapp.webmodules[url]['desc']
    ret.extend(webapp.webmodules[url]['arguments'])

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

    return {"signature": ret, "desc": desc, "testsets": ts}


@weblocation('/testing/testsets')
def testsets(url):
    ret = []

    try:
        webapp = application.modules[url]
    except:
        raise RequestInvalid("The URL <%s> not found" % url)

    _testsets = webapp.testsets[url]
    for testset in _testsets:
        ret.append({
            "name": testset['name'],
            "desc": testset['desc']
        })

    return ret


@weblocation("/testing/dummy")
def dummy():
    return {
        "desc": "Dummy"
    }