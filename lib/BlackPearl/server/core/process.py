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
import inspect
import os

from enum import Enum


_process = []


def add_process(process):
    _process.append(process)


def delete_process(process):
    for i in range(len(_process) - 1, -1, -1):
        if _process[i] == process:
            del _process[i]

Status = Enum("Status", "NOTSTARTED, STARTING, STARTFAILED, STARTED, STOPPING, RESTARTING, STOPPED, TERMINATED")


class Process:

    def __init__(self, name, command, env=None):
        self.name = name
        self.command = command
        self.process = None
        self.process_stop_event = asyncio.Event()
        self._status = Status.NOTSTARTED
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
        for i in range(0, len(self.listeners)):
            try:
                self.listeners[i](status)
            except:
                print("ERROR : Error invoking status listener added to <%s> process" % self.name)
                error = traceback.format_exc()
                print("ERROR : %s" % error)

    def add_status_listener(self, callback):
        args = len(inspect.signature(callback).parameters)
        if args != 1:
            error = "The callback function should have 1 argument but passed function has %s" % args
            print("INFO: %s" % error)
            raise ValueError(error)
        self.listeners.append(callback)

    def remove_status_listener(self, callback):
        for i in range(0, len(self.listeners)):
            if self.listeners[i] == callback:
                del self.listeners[i]
                return True
        return False

    @asyncio.coroutine
    def start(self):
        if not (self._status == Status.NOTSTARTED or self._status == Status.STOPPED
                or self._status == Status.TERMINATED or self._status == Status.STARTFAILED
                or self._status == Status.RESTARTING):
            raise InvalidState(
                "ERROR: Process <%s> is in <%s>."
                " The process can be started only while it "
                "in <%s> state" % (
                    self.name, self._status.name,
                    "%s, %s, %s, %s or %s" % (
                        Status.NOTSTARTED.name, Status.STOPPED.name, Status.TERMINATED.name,
                        Status.STARTFAILED.name, Status.RESTARTING.name
                    )
                )
            )
        try:
            add_process(self)
            self._set_status(Status.STARTING)
            inull = open("/dev/null", "r")

            self.process_stop_event.clear()
            self.process = yield from asyncio.create_subprocess_exec(
                *self.command, stdin=inull,
                stdout=sys.stdout, stderr=sys.stderr,
                env=self.env
            )

            self._set_status(Status.STARTED)
            s = yield from self.process.wait()
            if s != 0:
                print("ERROR: Process <%s> terminated "
                      "with non zero return code <%s>." % (self.name, s))
                if self._status != Status.RESTARTING:
                    self._set_status(Status.TERMINATED)
            else:
                print("INFO: Process <%s> stopped." % (
                    self.name))
                if self._status != Status.RESTARTING:
                    self._set_status(Status.STOPPED)
        except Exception as e:
            error = traceback.format_exc()
            print("ERROR: %s" % e)
            print("ERROR: %s" % error)
            self._set_status(Status.STARTFAILED)
        finally:
            self.process_stop_event.set()
            delete_process(self)

    @asyncio.coroutine
    def restart(self):
        self._set_status(Status.RESTARTING)
        try:
            yield from self.stop()
            yield from self.start()
        except InvalidState as e:
            error = traceback.format_exc()
            print("ERROR: %s" % e)
            print("ERROR: %s" % error)
            return

    def is_running(self):
        if self._status == Status.STOPPING:
            return True
        if self._status == Status.RESTARTING:
            raise NotRestartedYet("ERROR: %s is restarting" % self.name)
        if self._status == Status.NOTSTARTED:
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
        if self._status == Status.STARTED or self._status == Status.RESTARTING:
            if self._status != Status.RESTARTING:
                self._set_status(Status.STOPPING)
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
            raise InvalidState(
                "ERROR: Process <%s> is in <%s>."
                " The process can be stopped only while it "
                "in <%s or %s> state" % (
                    self.name, self._status, Status.STARTED.name, Status.RESTARTING.name
                )
            )

    @asyncio.coroutine
    def terminate(self):
        if self._status == Status.STARTED:
            self._set_status(Status.STOPPING)
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
                               "in <%s> state" % (self.name, self._status, Status.STARTED))

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