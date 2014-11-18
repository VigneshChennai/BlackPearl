#!/usr/bin/python

import threading
import multiprocessing
import time
import os
import subprocess
import signal

from server.exceptions import NotStartedYet

_process = []
_process_lock = threading.Lock()

def add_process(process):
    with _process_lock:
        _process.append(process)

def delete_process(process):
    with _process_lock:
    
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
        
    def start(self):
        def _start():
            try:
                add_process(self)
                try:
                    null = open("/dev/null", "w")
                    inull = open("/dev/null", "r")
                except:
                    null = open("nul", "w")
                    inull = open("nul", "r")                    
                process = subprocess.Popen(self.command, 
                                           stdin = inull, 
                                           stdout = null,
                                           stderr = null)
                self.pid = process.pid
                s = process.wait()
                if s != 0:
                    print("ERROR: Process <%s> terminated " \
                            "with non zero return code <%s>." % (self.name, s))
                    self._set_status("TERMINATED")
                else:
                    print("INFO: Process <%s> stopped gracefully." % (
                                                                   self.name))
                    self._set_status("STOPPED")
            finally:
                delete_process(self)
        t = threading.Thread(target=_start)
        t.start()
        
    def isrunning(self):
        return self._isrunning()
    
    def _isrunning(self):
        if self.pid == None:
            raise NotStartedYet("ERROR: %s not started yet" % (self.name))
        try:
            os.kill(self.pid, 0)
            return True
        except:
            return False
            
    def _isstopped(self):
        count = self.sig_timeout
        while count > 0:
            if self._isrunning():
                count -= 1
                time.sleep(1)
            else:
                return True
        return False
        
    def stop(self):
        if not self._isrunning():
            print("ERROR: Process <%s> is already stopped." \
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.pid, signal.SIGINT)
        if not self._isstopped():
            print("ERROR: Process <%s> not stopped with " \
                  "SIGINT signal, killing the process" % self.name)        
            self.kill()
        return True
        
    def terminate(self):
        if not self._isrunning():
            print("ERROR: Process <%s> is already stopped." \
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.pid, signal.SIGTERM)
        if not self._isstopped():
            print("ERROR: Process <%s> not stopped with " \
                  "SIGTERM signal, killing the process" % self.name)         
            self.kill()
        return True
    
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

