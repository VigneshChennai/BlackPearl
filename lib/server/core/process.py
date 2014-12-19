#!/usr/bin/python

import time
import os
import sys
import asyncio
import signal
import traceback

from server.exceptions import NotStartedYet, NotRestartedYet, InvalidState

_process = []

def add_process(process):
    _process.append(process)

def delete_process(process):
    for i in range(len(_process)-1, -1, -1):       
        if _process[i] == process:
            del _process[i]

class Process:

    def __init__(self, name, command, sig_timeout=15):
        self.name = name
        self.command = command
        self.pid = None
        self.status = "NOTSTARTED"
        self.sig_timeout = sig_timeout
    
    def _set_status(self, status):
        self.status = status
        
    @asyncio.coroutine
    def start(self):
        if not (self.status == 'NOTSTARTED' or self.status == 'STOPPED'
             or self.status == 'TERMINATED' or self.status == 'STARTFAILED'
             or self.status == 'RESTARTING'):
            raise InvalidState("ERROR: Process <%s> is in <%s>."\
                    " The process can be started only while it "\
                    "in <NOTSTARTED or STOPPED or TERMINATED or STARTFAILED, RESTARTING> state" % (self.name, self.status))
        try:
            add_process(self)
            self.status = 'STARTING'
            inull = open("/dev/null", "r")                 
            process = yield from asyncio.create_subprocess_exec(*self.command, 
                                       stdin = inull, 
                                       stdout = sys.stdout,
                                       stderr = sys.stderr)
            self.pid = process.pid
            self._set_status("STARTED")            
            s = yield from process.wait()
            if s != 0:
                print("ERROR: Process <%s> terminated " \
                        "with non zero return code <%s>." % (self.name, s))
                if self.status != "RESTARTING":
                    self._set_status("TERMINATED")
            else:
                print("INFO: Process <%s> stopped gracefully." % (
                                                               self.name))
                if self.status != "RESTARTING":
                    self._set_status("STOPPED")
        except Exception as e:
            error = traceback.format_exc()
            print("ERROR: %s" % e)
            print("ERROR: %s" % error)
            self.status = "STARTFAILED"
        finally:
            delete_process(self)
    
    @asyncio.coroutine
    def restart(self):
        self._set_status("RESTARTING")
        try:
            yield from self.stop()
            yield from self.start()
        except InvalidState as e:
            error = traceback.format_exc()
            print("ERROR: %s" % e)
            print("ERROR: %s" % error)
            return
    
    def isrunning(self):
        if self.status == 'STOPPING':
            return True
        if self.status == 'RESTARTING':
            raise NotRestartedYet("ERROR: %s is restarting" % (self.name))
        if self.status  == "NOTSTARTED":
            raise NotStartedYet("ERROR: %s not started yet" % (self.name))
        return self._isrunning()
    
    def _isrunning(self):
        if self.pid:
            try:
                os.kill(self.pid, 0)
                return True
            except:
                return False
        else:
            return False
    
    @asyncio.coroutine
    def _isstopped(self):
        count = self.sig_timeout
        while count > 0:
            if self._isrunning():
                yield from asyncio.sleep(1)
                count = count - 1
            else:
                break
        return
        
    @asyncio.coroutine
    def stop(self):
        if self.status == 'STARTED' or self.status == 'RESTARTING':
            self.status == 'STOPPING'
            if not self._isrunning():
                print("ERROR: Process <%s> is already stopped." \
                      " Ignoring stop request" % self.name)
                return False
            os.kill(self.pid, signal.SIGINT)
            yield from self._isstopped()
            if self._isrunning():
                print("ERROR: Process <%s> not stopped with " \
                      "SIGINT signal, killing the process" % self.name)        
                self.kill()
            return True
        else:
            raise InvalidState("ERROR: Process <%s> is in <%s>."\
                    " The process can be stopped only while it "\
                    "in <STARTED or RESTARTING> state" % (self.name, self.status))
        
    @asyncio.coroutine
    def terminate(self):
        if self.status == 'STARTED':
            self.status == 'STOPPING'
            if not self._isrunning():
                print("ERROR: Process <%s> is already stopped." \
                      " Ignoring stop request" % self.name)
                return False
            os.kill(self.pid, signal.SIGTERM)
            yield from self._isstopped()
            if self._isrunning():
                print("ERROR: Process <%s> not stopped with " \
                      "SIGTERM signal, killing the process" % self.name)         
                self.kill()
            return True
        else:
            raise InvalidState("ERROR: Process <%s> is in <%s>."\
                    " The process can be terminated only while it "\
                    "in <STARTED> state" % (self.name, self.status))
    
    def kill(self):
        if not self._isrunning():
            print("ERROR: Process <%s> is already stopped." \
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.pid, signal.SIGKILL)
        return True
    
    def send_signal(self, sig):
        if not self._isrunning():
            print("ERROR: Process <%s> is already stopped." \
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.pid, sig)
        return True

