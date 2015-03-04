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
import functools


from datetime import datetime
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

        self.status_listener_cb = None

    @property
    def status(self):
        return self._status

    def _set_status(self, status):
        print("DEBUG: Status of process <%s> is <%s>" % (self.name, status))
        self._status = status
        if self.status_listener_cb:
            try:
                print("DEBUG: Calling status listener callback for process <%s>." % self.name)
                self.status_listener_cb(status)
                print("DEBUG: Calling status listener callback for process <%s> successful" % self.name)
            except:
                print("ERROR : Error invoking status listener callback of process <%s>" % self.name)
                error = traceback.format_exc()
                print("ERROR : %s" % error)

    def set_status_listener(self, callback):
        print("DEBUG: Adding status listener for process <%s>" % self.name)
        args = len(inspect.signature(callback).parameters)
        if args != 1:
            error = "The callback function should have 1 argument but passed function has %s" % args
            print("INFO: %s" % error)
            raise ValueError(error)
        self.status_listener_cb = callback

    @asyncio.coroutine
    def start(self):
        if not (self._status == Status.NOTSTARTED or self._status == Status.STOPPED
                or self._status == Status.TERMINATED or self._status == Status.STARTFAILED):
            raise InvalidState(
                "ERROR: Process <%s> is in <%s>."
                " The process can be started only while it "
                "in <%s> state" % (
                    self.name, self._status.name,
                    "%s, %s, %s or %s" % (
                        Status.NOTSTARTED.name, Status.STOPPED.name, Status.TERMINATED.name,
                        Status.STARTFAILED.name
                    )
                )
            )
        try:
            add_process(self)
            while True:
                self._set_status(Status.STARTING)
                null_device = open("/dev/null", "r")

                self.process_stop_event.clear()
                self.process = yield from asyncio.create_subprocess_exec(
                    *self.command, stdin=null_device,
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
                        break
                else:
                    print("INFO: Process <%s> stopped." % (
                        self.name))
                    if self._status != Status.RESTARTING:
                        self._set_status(Status.STOPPED)
                        break

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
            # Process will be restarting
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
                self.process.send_signal(0)
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
            self.process.send_signal(signal.SIGINT)
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
            self.process.send_signal(signal.SIGTERM)
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
        self.process.send_signal(signal.SIGKILL)
        return True

    def send_signal(self, sig):
        if not self._is_running():
            print("ERROR: Process <%s> is already stopped."
                  " Ignoring stop request" % self.name)
            return False
        self.process.send_signal(sig)
        return True


class ServerProcess(Process):

    def __init__(self, name, command, env=None, restart_on_crash=True, startup_crash_limit=3, startup_secs=30):
        Process.__init__(self, name, command, env)
        self.start_time = None
        self.last_crashed = None
        self.crash_count = 0
        self.successive_startup_crash_count = 0
        self.crash_history = []

        self.restart_on_crash = restart_on_crash
        self.startup_secs = startup_secs
        self.startup_crash_limit = startup_crash_limit

        self._server_status = Status.NOTSTARTED

    @property
    def status(self):
        return self._server_status

    def _set_status(self, status):
        self._status = status
        if status == Status.STARTED:
            self._set_server_status(Status.STARTED)

    def _set_server_status(self, status):
        self._server_status = status
        if self.status_listener_cb:
            try:
                self.status_listener_cb(status)
            except:
                print("ERROR : Error invoking status listener callback of process <%s>" % self.name)
                error = traceback.format_exc()
                print("ERROR : %s" % error)

    def set_status_listener(self, callback):
        args = len(inspect.signature(callback).parameters)
        if args != 1:
            error = "The callback function should have 1 argument but passed function has %s" % args
            print("INFO: %s" % error)
            raise ValueError(error)
        self.status_listener_cb = callback

    @asyncio.coroutine
    def start(self):
        while True:
            self._set_server_status(Status.STARTING)
            self.start_time = datetime.now()
            yield from Process.start(self)

            if self._server_status == Status.STARTING:
                self._set_server_status(Status.STARTFAILED)
            elif self._server_status == Status.STARTED:
                print("WARNING: The process <%s> stopped/crashed unexpectedly" % self.name)
                self.last_crashed = datetime.now()
                self.crash_count += 1
                self.crash_history.append(self.last_crashed)

                run_duration = self.last_crashed - self.start_time
                if run_duration.total_seconds() < self.startup_secs:
                    self.successive_startup_crash_count += 1
                else:
                    self.successive_startup_crash_count = 0

                if not self.restart_on_crash:
                    break

                if self.startup_crash_limit > self.successive_startup_crash_count:
                    print("INFO: The process is configured to restart on crash.")
                    print("INFO: Restarting the process <%s>" % self.name)
                else:
                    print("INFO: Process <%s> failed to startup after <%s> attempts" % (
                        self.name, self.startup_crash_limit))
                    self._set_server_status(Status.STARTFAILED)
                    break
            else:
                if self._status == Status.STOPPED:
                    self._set_server_status(Status.STOPPED)
                else:  # if Status.TERMINATED
                    self._set_server_status(Status.TERMINATED)

    @asyncio.coroutine
    def stop(self, timeout=15):
        self._set_server_status(Status.STOPPING)
        yield from Process.stop(self)

    @asyncio.coroutine
    def terminate(self):
        self._set_server_status(Status.STOPPING)
        yield from Process.terminate(self)

    @asyncio.coroutine
    def restart(self):
        self._set_server_status(Status.RESTARTING)
        yield from Process.restart(self)


class ProcessGroup:

    def __init__(self, name, stop_all_on_one_crashed=True):
        self.name = name
        self._status = Status.NOTSTARTED
        self.status_listener_cb = None
        self.processes = {}
        self.stop_all_on_one_crashed = stop_all_on_one_crashed

    @property
    def status(self):
        return self._status

    def _set_status(self, status):
        self._status = status

        if self.status_listener_cb:
            try:
                self.status_listener_cb(status)
            except:
                print("ERROR : Error invoking status listener callback of process <%s>" % self.name)
                error = traceback.format_exc()
                print("ERROR : %s" % error)

    def set_status_listener(self, callback):
        args = len(inspect.signature(callback).parameters)
        if args != 1:
            error = "The callback function should have 1 argument but passed function has %s" % args
            print("INFO: %s" % error)
            raise ValueError(error)
        self.status_listener_cb = callback

    def add_process(self, name, command, env=None):
        def set_process_status(status):
            self.processes[process] = status
            if status in (Status.STOPPED, Status.TERMINATED, Status.STARTFAILED) and self._status != Status.STOPPING:
                if process in self.processes:
                    if self.stop_all_on_one_crashed:
                        print("WARNING: Stopping all the process in the ProcessGroup<%s>" % self.name)
                        asyncio.async(self.stop())

            else:
                if self._status == Status.STARTING:
                    started = True
                    for p in self.processes:
                        if p.status == Status.STARTING:
                            started = False
                            if self._status != Status.STARTING:
                                self._set_status(Status.STARTING)
                            break

                    if started:
                        self._set_status(Status.STARTED)

        process = Process(name, command, env)
        process.set_status_listener(set_process_status)
        self.processes[process] = process.status

    def remove_process(self, process):
        try:
            del self.processes[process]
        except:
            raise ValueError("The process<%s> is not added to the "
                             "ProcessGroup<%s>" %(process.name, self.name)) from None

    @asyncio.coroutine
    def start(self):
        if self.status not in (Status.NOTSTARTED, Status.STOPPED, Status.TERMINATED, Status.STARTFAILED):
            raise InvalidState(
                "ERROR: ProcessGroup <%s> is in <%s>."
                " The ProcessGroup can be started only while it "
                "in <%s> state" % (
                    self.name, self._status.name,
                    "%s, %s, %s or %s" % (
                        Status.NOTSTARTED.name, Status.STOPPED.name, Status.TERMINATED.name,
                        Status.STARTFAILED.name
                    )
                )
            )
        while True:
            self._set_status(Status.STARTING)
            tasks = [asyncio.async(p.start()) for p in self.processes.keys()]
            done, pending = yield from asyncio.wait(tasks)
            if self._status != Status.RESTARTING:
                break
        self._set_status(Status.STOPPED)

    @asyncio.coroutine
    def stop(self):
        self._set_status(Status.STOPPING)
        tasks = [asyncio.async(p.stop()) for p in self.processes.keys()]

        def cb(future):
            try:
                future.result()
            except:
                pass

        for task in tasks:
            task.add_done_callback(cb)

        yield from asyncio.wait(tasks)

    @asyncio.coroutine
    def terminate(self):
        yield from self.stop()

    @asyncio.coroutine
    def restart(self):
        self._set_status(Status.RESTARTING)
        try:
            yield from self.stop()
            # Process will be restarting
        except InvalidState as e:
            error = traceback.format_exc()
            print("ERROR: %s" % e)
            print("ERROR: %s" % error)
            return

    def is_running(self):
        for status in self.processes.values():
            if status in (Status.STARTED, Status.STOPPING, Status.RESTARTING):
                return True

        return False


class NotStartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class NotRestartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class InvalidState(Exception):
    def __init__(self, msg):
        super().__init__(msg)