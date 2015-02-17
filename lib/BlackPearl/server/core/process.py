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

import sys
import asyncio
import signal
import traceback

import os


_process = []


def add_process(process):
    _process.append(process)


def delete_process(process):
    for i in range(len(_process) - 1, -1, -1):
        if _process[i] == process:
            del _process[i]


class Process:
    def __init__(self, name, command, env=None):
        self.name = name
        self.command = command
        self.process = None
        self.process_stop_event = asyncio.Event()
        self._status = "NOTSTARTED"
        if env:
            self.env = env
        else:
            self.env = {}

        self.listeners = []

    @property
    def status(self):
        return self._status

    def _set_status(self, status):
        self._status = status
        to_del = []
        for i in range(0, len(self.listeners)):
            try:
                ret = self.listeners[i](status)
            except:
                print("ERROR : Error invoking status listener added to <%s> process" % self.name)
                error = traceback.format_exc()
                print("ERROR : %s" % error)
            else:
                if not ret:
                    to_del.append(i)

        for i in to_del:
            del self.listeners[i]

    def add_status_listener(self, callback):
        self.listeners.append(callback)

    @asyncio.coroutine
    def start(self):
        if not (self._status == 'NOTSTARTED' or self._status == 'STOPPED'
                or self._status == 'TERMINATED' or self._status == 'STARTFAILED'
                or self._status == 'RESTARTING'):
            raise InvalidState("ERROR: Process <%s> is in <%s>."
                               " The process can be started only while it "
                               "in <NOTSTARTED or STOPPED or TERMINATED or STARTFAILED, RESTARTING> state"
                               % (self.name, self._status))
        try:
            add_process(self)
            self._set_status('STARTING')
            inull = open("/dev/null", "r")

            self.process_stop_event.clear()
            self.process = yield from asyncio.create_subprocess_exec(
                *self.command, stdin=inull,
                stdout=sys.stdout, stderr=sys.stderr,
                env=self.env
            )

            self._set_status("STARTED")
            s = yield from self.process.wait()
            if s != 0:
                print("ERROR: Process <%s> terminated "
                      "with non zero return code <%s>." % (self.name, s))
                if self._status != "RESTARTING":
                    self._set_status("TERMINATED")
            else:
                print("INFO: Process <%s> stopped gracefully." % (
                    self.name))
                if self._status != "RESTARTING":
                    self._set_status("STOPPED")
        except Exception as e:
            error = traceback.format_exc()
            print("ERROR: %s" % e)
            print("ERROR: %s" % error)
            self._set_status("STARTFAILED")
        finally:
            self.process_stop_event.set()
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

    def is_running(self):
        if self._status == 'STOPPING':
            return True
        if self._status == 'RESTARTING':
            raise NotRestartedYet("ERROR: %s is restarting" % self.name)
        if self._status == "NOTSTARTED":
            raise NotStartedYet("ERROR: %s not started yet" % self.name)
        return self._is_running()

    def _is_running(self):
        if self.process and self.process.pid >= 0:
            try:
                os.kill(self.process.pid, 0)
                return True
            except:
                return False
        else:
            return False

    @asyncio.coroutine
    def _is_stopped(self, timeout):
        yield from asyncio.wait_for(self.process_stop_event.wait(), timeout)
        if self._is_running():
            return False
        return True

    @asyncio.coroutine
    def stop(self, timeout=15):
        if self._status == 'STARTED' or self._status == 'RESTARTING':
            if self._status != 'RESTARTING':
                self._set_status('STOPPING')
            if not self._is_running():
                print("ERROR: Process <%s> is already stopped."
                      " Ignoring stop request" % self.name)
                return False
            os.kill(self.process.pid, signal.SIGINT)
            yield from self._is_stopped(timeout)
            if self._is_running():
                print("ERROR: Process <%s> not stopped with "
                      "SIGINT signal, killing the process" % self.name)
                self.kill()
            return True
        else:
            raise InvalidState("ERROR: Process <%s> is in <%s>."
                               " The process can be stopped only while it "
                               "in <STARTED or RESTARTING> state" % (self.name, self._status))

    @asyncio.coroutine
    def terminate(self):
        if self._status == 'STARTED':
            self._set_status('STOPPING')
            if not self._is_running():
                print("ERROR: Process <%s> is already stopped."
                      " Ignoring stop request" % self.name)
                return False
            os.kill(self.process.pid, signal.SIGTERM)
            yield from self._is_stopped()
            if self._is_running():
                print("ERROR: Process <%s> not stopped with "
                      "SIGTERM signal, killing the process" % self.name)
                self.kill()
            return True
        else:
            raise InvalidState("ERROR: Process <%s> is in <%s>."
                               " The process can be terminated only while it "
                               "in <STARTED> state" % (self.name, self._status))

    def kill(self):
        if not self._is_running():
            print("ERROR: Process <%s> is already stopped."
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.process.pid, signal.SIGKILL)
        return True

    def send_signal(self, sig):
        if not self._is_running():
            print("ERROR: Process <%s> is already stopped."
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.process.pid, sig)
        return True


class NotStartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class NotRestartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class InvalidState(Exception):
    def __init__(self, msg):
        super().__init__(msg)