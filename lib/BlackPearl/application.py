#!/usr/bin/env python

import sys
import os
import traceback
import json
import cgi

from http.cookies import SimpleCookie

from BlackPearl.core import utils
from BlackPearl.core import sessions
from BlackPearl.core import exceptions
from BlackPearl.core import webapps
from BlackPearl.core import urls


def __application__(environ, start_response):
    #Request method (POST, GET .. etc)
    method = environ['REQUEST_METHOD']
    urlpath = environ['PATH_INFO']
    
    #Parsing the input values.
    #The FieldStorage will handle all methods and file upload as well.
    formvalues = cgi.FieldStorage(fp=environ['wsgi.input'],environ=environ)
    
    try:
        handler = None
        #Restricting the access method only to GET and POST
        if not (method == 'GET' or method == 'POST'):
            status = '405 Method Not Allowed'
            start_response(status, [('Allow',('POST', 'GET'))])
            return [str("Method<%s> is not allowed" % (method)).encode('utf-8')]

        try:
            webapp = webapps.modules[urlpath]
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
                preprocessor(session, urlpath)
        except exceptions.RequestCannotBeProcessed as e:
            status = "200 ok"
            start_response(status, [])
            rets = {
            "status" : -101,
            "desc" : str(e)
            }
            return [rets.encode('UTF-8')]
        except:
            status = "200 ok"
            start_response(status, [])
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
                posthandler(session, urlpath, rets)
        except:
            status = "200 ok"
            start_response(status, [])
            rets = {
            "status" : -301,
            "desc" : "Exception occured in posthandler <%s>."\
                " Error: <%s>" %(str(posthandler), str(e))
            }
            return [json.dumps(rets).encode('UTF-8')]
    except Exception as e:
        error = traceback.format_exc()
        status = '500 Internal Server Error Occured' 
        start_response(status, [])
        return [error.encode('utf-8')]
    
    #serializing the python object return from handler to JSON.
    try:
        json_rets = json.dumps(rets)
        status = "200 ok"
    except:
        status = "500 Error in code"
        start_response(status, [])
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
        start_response(status, [])
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

def app_server(webappfolder):
    #initializing the webapps
    webapps.initialize(webappfolder)
    return __application__

#This "application" is call for every request by the appserver (uwsgi)
application = app_server(os.environ['BLACKPEARL_APPS'])

