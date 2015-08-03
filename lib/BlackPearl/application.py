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

import traceback
import json
import cgi
import pickle
import inspect
import os
import base64
import logging

from BlackPearl import testing
from BlackPearl.core import sessions
from BlackPearl.core import exceptions
from BlackPearl.core import utils
from BlackPearl.core.exceptions import RequestInvalid, UnSuccessfulException

logger = logging.getLogger(__name__)
webapp = None


def invoke_preprocessors(urlpath, session):
    try:
        # Executing all the preprocessors defined and configured in webapp
        url = urlpath.replace(webapp.url_prefix, "")
        for preprocessor in webapp.preprocessors:
            preprocessor['func'](session, url)
        return None
    except exceptions.RequestCannotBeProcessed as e:
        rets = {
            "status": -101,
            "desc": str(e)
        }
    except exceptions.UnAuthorizedAccess as e:
        rets = {
            "status": -102,
            "desc": str(e)
        }
    except Exception as e:
        rets = {
            "status": -103,
            "desc": "Exception occurred in Preprocessor. Error: <%s>" % str(e)
        }

    return rets


def invoke_posthandlers(urlpath, session, rets):
    # Invoking the post handler defined and configured in webapp
    try:
        for posthandler in webapp.posthandlers:
            posthandler['func'](session, urlpath, rets)
        return None
    except Exception as e:
        error = {
            "status": -301,
            "desc": "Exception occurred in posthandler. Error: <%s>" % e
        }
        return error


def handle_request(module, session, parameter):
        """This function handles the user request"""
        func = module['func']
        signature = module['signature']

        try:
            parameter = utils.validate_parameter(signature, parameter)
        except Exception as e:
            raise ParametersInvalid(str(e)) from None

        return func(session, parameter)


def return_to_client(start_response, headers, session, data):
    status = "200 ok"
    # serializing the python object return from handler to JSON.
    try:
        json_rets = json.dumps(data)
    except:
        start_response(status, headers)
        rets = {
            "status": -401,
            "desc": "Error in serializing the return data from module. Return value <%s>" % (str(data))
        }
        yield json.dumps(rets).encode('UTF-8')
    else:
        # Encrypting the session object
        sess_value = sessions.encode_session(session).decode('utf-8') + "; Path=/"

        # Most browser supports only around 400O bytes in the cookie.
        # So, it is always good practise to have less value in the cookie

        # restricting the session object size to 4000
        if len(sess_value) > 4000:
            start_response(status, headers)
            rets = {"status": -501,
                    "desc": "Session object should be less than 4000 bytes in size. "
                            "Currently the session object size is <%s> bytes" % (len(sess_value))}
            yield json.dumps(rets).encode('UTF-8')
        else:
            # Once everything went well, we are sending the result to the client
            headers.append(('Set-Cookie', "session=%s" % sess_value))
            start_response(status, headers)
            yield json_rets.encode('UTF-8')


class ParametersInvalid(Exception):
    """This exception should be raised when invalid parameters are received"""
    pass


def __application__(environ, start_response):
    headers = [('Content-Type', "text/plain")]

    try:
        # Request method (POST, GET .. etc)
        method = environ['REQUEST_METHOD']
        urlpath = environ['PATH_INFO']

        # Parsing the input values.
        # The FieldStorage will handle all methods and file upload as well.
        form_values = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
        # Restricting the access method only to GET and POST
        if not (method == 'GET' or method == 'POST'):
            status = '405 Method Not Allowed'
            start_response(status, headers + [('Allow', ('POST', 'GET'))])
            yield str("Method<%s> is not allowed" % method).encode('UTF-8')

        else:
            try:
                module = webapp.webmodules[urlpath]
            except:
                status = '404 Requested URL not found'
                start_response(status, headers)
                yield str("Requested URL not found : %s" % (urlpath)).encode('utf-8')
            else:
                # Parse/Initialize session object.
                session = sessions.parse_session(environ=environ)
                headers = [('Content-Type', "text/json")]

                error = invoke_preprocessors(urlpath=urlpath, session=session)
                if error:
                    for i in return_to_client(start_response=start_response, headers=headers,
                                              session=session, data=error):
                        yield i
                else:
                    # Invoking the request handler for this the URL
                    try:
                        output = handle_request(module=module, session=session, parameter=form_values)
                    except ParametersInvalid as e:
                        rets = {
                            "status": -201,
                            "desc": str(e)
                        }
                        for i in return_to_client(start_response=start_response, headers=headers,
                                                  session=session, data=rets):
                            yield i
                    except RequestInvalid as ri:
                        rets = {
                            "status": -202,
                            "desc": str(ri)
                        }
                        for i in return_to_client(start_response=start_response, headers=headers,
                                                  session=session, data=rets):
                            yield i
                    except UnSuccessfulException as e:
                        rets = {
                            "status": -203,
                            "desc": e.desc,
                            "data": e.data
                        }
                        for i in return_to_client(start_response=start_response, headers=headers,
                                                  session=session, data=rets):
                            yield i
                    except Exception:
                        error = traceback.format_exc()
                        rets = {
                            "status": -299,
                            "desc": error
                        }
                        for i in return_to_client(start_response=start_response, headers=headers,
                                                  session=session, data=rets):
                            yield i
                    else:
                        if inspect.isgenerator(output):
                            status = "200 ok"
                            headers = []
                            try:
                                remaining = None
                                for data_segment in output:
                                    if type(data_segment) == tuple:
                                        headers.append(data_segment)
                                    else:
                                        remaining = data_segment
                            except:
                                status = "500 Internal server error. Check the server logs"
                                logger.error("Error occurred while setting header for file output.")
                                logger.error("ERROR:", traceback.format_exc())
                                start_response(status, [])
                                yield traceback.format_exc().encode('UTF-8')
                            else:
                                try:
                                    start_response(status, headers)
                                    yield remaining
                                    for data_segment in output:
                                        yield data_segment
                                except:
                                    logger.error("Error occurred while returning file output.")
                                    logger.error("ERROR:", traceback.format_exc())
                        else:
                            rets = {
                                "status": 0,
                                "data": output
                            }
                            error = invoke_posthandlers(urlpath=urlpath, session=session, rets=rets)
                            if error:
                                rets = error
                            for i in return_to_client(start_response=start_response, headers=headers,
                                                      session=session, data=rets):
                                yield i

    except:
        error = traceback.format_exc()
        status = '200 ok'
        start_response(status, headers)
        rets = {
            "status": -1,
            "desc": error
        }
        yield json.dumps(rets).encode('utf-8')


def initialize():
    global webapp, BLOCK_SIZE, AES_KEY
    # initializing the webapps from the pickled file.
    sessions.BLOCK_SIZE = int(os.environ['BLACKPEARL_ENCRYPT_BLOCK_SIZE'])
    sessions.AES_KEY = base64.b64decode(os.environ['BLACKPEARL_ENCRYPT_KEY'])
    testing.listen = os.environ['BLACKPEARL_LISTEN']
    pickle_file = os.environ['BLACKPEARL_PICKLE_FILE']
    pfile = open("%s" % pickle_file, "rb")
    with pfile:
        webapp = pickle.load(pfile)

    # We are generating signature object during initialization because, signature
    # object is not picklable
    for webmodule in webapp.webmodules.values():
        webmodule["signature"] = inspect.signature(webmodule["handler"])


# This "application" is called for every request by the app_server (uwsgi)
application = __application__
