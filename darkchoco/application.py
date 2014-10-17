#!/usr/bin/env python

import sys
import os
import traceback
import json
import cgi

from darkchoco.core import utils
from darkchoco.core import sessions
from darkchoco.core import exceptions
from darkchoco.core import webapps
from darkchoco.core import urls

def __application__(environ, start_response):
    method = environ['REQUEST_METHOD']
    urlpath = environ['PATH_INFO']
    formvalues = cgi.parse(environ=environ)
    
    try:
        handler = None

        #Restricting the access method only to GET and POST
        if not (method == 'GET' or method == 'POST'):
            status = '405 Method Not Allowed'
            start_response(status, [('Allow',('POST', 'GET'))])
            return [str("Method<%s> is not allowed" % (method)).encode('utf-8')]

        try:
            webapp = webapps.get_webapp(urlpath)
        except ValueError as e:
            status = '404 Requested URL not found'
            start_response(status, [])
            return [str(e).encode('utf-8')]   
            
        if webapp.session_enabled:
            #session.__status__ attribute can have one among the below three 
            #values
            #
            #session.__status__ = "fetched" --> When the session exist in 
            #                                   session cache
            #session.__status__ = "recreated" --> When the session does not 
            #                                   exits in the session cache
            #session.__status__ = "created" --> When the session id is not
            #                                    in the cookie
            try:
                session_id = [utils.parseCookie(
                                environ.get("HTTP_COOKIE","")
                                )["session_id"]][0]
                session = sessions.get_session(webapp, session_id)
                session.__status__ = "fetched"
                if session == None:
                    session = sessions.Session(webapp)
                    session.__status__ = "recreated"
                    session_id = session.__id__
                    
            except:
                session = sessions.Session(webapp)
                session.__status__ = "created"
                session_id = session.__id__
        else:
            session = None
            
        try:
            for preprocessor in webapp.preprocessors:
                preprocessor(session, urlpath)
        except exceptions.RequestCannotBeProcessed as e:
            status = "200 ok"
            start_response(status, [])
            rets = {
            "status" : -1,
            "desc" : str(e)
            }
            return [rets.encode('UTF-8')]
        except:
            status = "200 ok"
            start_response(status, [])
            rets = {
            "status" : -2,
            "desc" : "Exception occured in Preprocessor. Error: <%s>" %(str(e))
            }
            return [rets.encode('UTF-8')]
        
        rets = webapp.handle_request(session, urlpath, formvalues)         
        try:
            for posthandler in webapp.posthandlers:
                posthandler(session, urlpath, rets)
        except:
            status = "200 ok"
            start_response(status, [])
            rets = {
            "status" : -2,
            "desc" : "Exception occured in posthandler <%s>."\
                " Error: <%s>" %(str(posthandler), str(e))
            }
            return [rets.encode('UTF-8')]
    except Exception as e:
        error = traceback.format_exc()
        status = '500 Internal Server Error Occured' 
        start_response(status, [])
        return [error.encode('utf-8')]
    
    status = "200 ok"
    json_rets = json.dumps(rets)
    if webapp.session_enabled:
        start_response(status,[('Set-Cookie', "session_id=%s" % (session_id))])
    else:
        start_response(status,[])
        
    return [json_rets.encode('UTF-8')]

def app_server(webappfolder):
     webapps_lst = webapps.get_app_details(webappfolder)
     urls.initialize(webapps_lst)
     sessions.initialize(webapps_lst)
     return __application__

application = app_server(os.environ['DARKCHOCO_APPS'])

