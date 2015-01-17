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

import sys
import os
import traceback
import json
import cgi
import pickle
import inspect

from http.cookies import SimpleCookie

from BlackPearl.core import utils
from BlackPearl.core import sessions
from BlackPearl.core import exceptions
from BlackPearl.core import webapps
from BlackPearl.core import security
from BlackPearl.testing import testing

modules = {}
deployed_webapps = []

def __application__(environ, start_response):

    #Request method (POST, GET .. etc)
    method = environ['REQUEST_METHOD']
    urlpath = environ['PATH_INFO']

    #Parsing the input values.
    #The FieldStorage will handle all methods and file upload as well.
    formvalues = cgi.FieldStorage(fp=environ['wsgi.input'],environ=environ)
    headers = [('Content-Type', "application/json")]
    try:
        handler = None
        #Restricting the access method only to GET and POST
        if not (method == 'GET' or method == 'POST'):
            status = '405 Method Not Allowed'
            start_response(status, [('Allow',('POST', 'GET'))])
            return [str("Method<%s> is not allowed" % (method)).encode('utf-8')]

        try:
            webapp = modules[urlpath]
        except KeyError as e:
            status = '404 Requested URL not found'
            start_response(status, [])
            return [str("Requested URL not found : %s" % (
                                urlpath)).encode('utf-8')]

        #session.__status__ attribute can have one among the below three
        #values
        #
        #session.__status__ = "fetched" --> When the session is not expired
        #session.__status__ = "recreated" --> When the session is expired
        #session.__status__ = "created" --> When the session is not

        cookie = SimpleCookie()
        cookie.load(environ.get("HTTP_COOKIE",""))

        try:
            cookie = SimpleCookie()
            cookie.load(environ.get("HTTP_COOKIE",""))

            #trying to get the cookie encrypted "session" from the cookie object
            #if not there, exception raised
            session_b64_enc = cookie["session"].value

            #trying to decode the encrypted session value
            session = sessions.decode_session(session_b64_enc)

            #if the session is None, then "session' value in the cookie
            #is invalid or it got exprired.
            if session == None:
                session = sessions.Session()
                session.__status__ = "recreated"
                session_id = session.__id__
            else:
                session.__status__ = "fetched"
        except:
            #When there is not session value in cookie,
            #new session cookie is created.
            session = sessions.Session(webapp)
            session.__status__ = "created"

        try:
            #Executing all the preprocessors defined and configured in webapp
            for preprocessor in webapp.preprocessors:
                preprocessor['func'](session, urlpath)
        except exceptions.RequestCannotBeProcessed as e:
            status = "200 ok"
            start_response(status, headers)
            rets = {
            "status" : -101,
            "desc" : str(e)
            }
            return [rets.encode('UTF-8')]
        except:
            status = "200 ok"
            start_response(status, headers)
            rets = {
            "status" : -102,
            "desc" : "Exception occured in Preprocessor. Error: <%s>" %(str(e))
            }
            return [json.dumps(rets).encode('UTF-8')]

        #Invoking the request handler for this the URL
        rets = webapp.handle_request(session, urlpath, formvalues)

        #Invoking the post handler defined and configured in webapp
        try:
            for posthandler in webapp.posthandlers:
                posthandler['func'](session, urlpath, rets)
        except:
            status = "200 ok"
            start_response(status, headers)
            rets = {
            "status" : -301,
            "desc" : "Exception occured in posthandler <%s>."\
                " Error: <%s>" %(str(posthandler), str(e))
            }
            return [json.dumps(rets).encode('UTF-8')]
    except Exception as e:
        error = traceback.format_exc()
        status = '500 Internal Server Error Occured'
        start_response(status, headers)
        return [error.encode('utf-8')]

    #serializing the python object return from handler to JSON.
    try:
        json_rets = json.dumps(rets)
        status = "200 ok"
    except:
        status = "200 ok"
        start_response(status, headers)
        rets = {
            "status" : -401,
            "desc" : "Error in serializing the return data from module."\
                     "Return value <%s>" % (str(rets))
            }
        return [json.dumps(rets).encode('UTF-8')]

    #Encrypting the session object
    sess_value = sessions.encode_session(session).decode('utf-8') + "; Path=/"

    #Most browser supports only around 400O bytes in the cookie.
    #So, it is always good practise to have less value in the cookie

    #restricting the session object size to 4000
    if len(sess_value) > 4000:
        start_response(status, headers)
        rets = {
            "status" : -501,
            "desc" : "Session object should be less than 4000 bytes in size."\
                     "Currently the session object size is <%s> bytes" % (
                                                                len(sess_value))
            }
        return [json.dumps(rets).encode('UTF-8')]

    #Once everything went well, we are sending the result to the client
    start_response(status,[('Set-Cookie', "session=%s" % (sess_value))])
    return [json_rets.encode('UTF-8')]

def initialize():
    global modules, deployed_webapps
    #initializing the webapps from the pickled file.
    print("Initializing webapps")
    temp = os.environ["BLACKPEARL_TMP"]
    security.BLOCK_SIZE = int(os.environ['BLACKPEARL_ENCRYPT_BLOCK_SIZE'])
    security.AES_KEY = os.environ['BLACKPEARL_ENCRYPT_KEY']
    testing.listen = os.environ['BLACKPEARL_LISTEN']
    pfile = open("%s/pickle/webapps" % temp, "rb")
    with pfile:
        deployed_webapps = pickle.load(pfile)

    #We are generating signature object during initialization because, signature
    #object is not picklable
    for webapp in deployed_webapps:
        for url, webmodule in webapp.webmodules.items():
            modules[url] = webapp
            webmodule["signature"] = inspect.signature(webmodule["handler"])


#This "application" is called for every request by the appserver (uwsgi)
application = __application__
