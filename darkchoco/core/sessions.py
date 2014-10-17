#!/usr/bin/env python

import random
import time
import threading

from darkchoco.core.decorators import runinterval

sessions = {}

session_retension = {}
amendment_lock = {}


#need to find a effective way to manage session in cache. Do check django
class Session:
    def __init__(self, webapp):
        self.created = time.time()
        self.lastaccessed = time.time()
        lock = amendment_lock[webapp.url_prefix]

        webapp_sessions = sessions[webapp.url_prefix]
        with lock:
            while True:
                rand = random.random()
                if rand not in webapp_sessions.keys():
                    webapp_sessions[str(rand)] = self
                    self.__id__ = str(rand)
                    break
        
    def accessed():
        self.lastaccessed = time.time()

def get_session(webapp, session_id):
    return sessions[webapp.url_prefix][session_id]

def initialize(webapps):
    for webapp in webapps:
        if webapp.session_enabled:
            sessions[webapp.url_prefix] = {}
            session_retension[webapp.url_prefix] = webapp.session_retension or (60 * 15)
            amendment_lock[webapp.url_prefix] = threading.Lock()

@runinterval(60)
def delete_old_session():
    for url_prefix, webapp_session in sessions.items():
        to_remove = []                                   
        for session_id in webapp_session.keys():
            session = webapp_session[session_id]
            if (time.time() - session.lastaccessed) \
                        > session_retension[url_prefix]:            
                to_remove.append(session_id)
                
        for session_id in to_remove:
            print("INFO: Clearing session <%s>" %(session_id))
            webapp_session.pop(session_id)

