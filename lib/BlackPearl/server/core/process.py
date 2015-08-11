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
import logging
from enum import Enum

_process = []

logger = logging.getLogger(__name__)

def add_process(process):
    _process.append(process)


def delete_process(process):
    for i in range(len(_process) - 1, -1, -1):
        if _process[i] == process:
            del _process[i]


class AsyncTask:

    def __init__(self):
        self.async_task_list = []

    def new_async_task(self, task):
        task_handler = asyncio.async(task)
        self.async_task_list.append(task_handler)
        return task_handler

    @asyncio.coroutine
    def wait_for_async_task_completion(self):
        while len(self.async_task_list) > 0:
            done, pending = yield from asyncio.wait(self.async_task_list, return_when=asyncio.FIRST_COMPLETED)
            to_del = []
            for i in range(0, len(self.async_task_list)):
                for task in done:
                    if task == self.async_task_list[i]:
                        to_del.append(i)
            to_del.sort(reverse=True)
            for i in to_del:
                del self.async_task_list[i]


Status = Enum("Status", "NOTSTARTED, STARTING, STARTFAILED, STARTED, STOPPING, RESTARTING, STOPPED, TERMINATED")


class ProcessStatus:
    def __init__(self, process_name, init_status=Status.NOTSTARTED):
        self._process_name = process_name
        self.__status__ = init_status
        self._status_cb_list = []

    @property
    def status(self):
        return self.__status__

    @classmethod
    def _get_module_path(cls, func):
        """This function returns the module in which the function is defined"""
        if isinstance(func, functools.partial):
            func = func.func

        if hasattr(func, "__self__"):
            return func.__name__ + " defined in class " + repr(func.__self__.__class__)

        mod = inspect.getmodule(func)
        if mod:
            for path, module in sys.modules.items():
                if mod == module:
                    return func.__name__ + " defined in module <" + path + ">"

    def __set_status__(self, status):
        logger.debug("Status of process <%s> is <%s>" % (self._process_name, status))
        self.__status__ = status
        if len(self._status_cb_list) > 0:
            try:
                for cb in self._status_cb_list:
                    cb(status)
            except:
                logger.error("Error invoking status listener callback of process <%s>" % self._process_name)
                error = traceback.format_exc()
                logger.error("%s" % error)

    def add_status_listener(self, callback):
        func = ProcessStatus._get_module_path(callback)
        logger.debug("Adding status listener <%s> for process <%s>" % (func, self._process_name))
        args = len(inspect.signature(callback).parameters)
        if args != 1:
            error = "The callback function <%s> should have 1 argument but passed function has %s" % (func, args)
            logger.info("%s" % error)
            raise ValueError(error)
        self._status_cb_list.append(callback)

    def remove_status_listener(self, callback):
        func = ProcessStatus._get_module_path(callback)
        logger.debug("Removing status listener <%s> for process <%s>" % (func, self._process_name))
        if callback in self._status_cb_list:
            del self._status_cb_list[callback]
        else:
            raise ValueError("The callback <%s> is not available in status change callback list" % repr(func))


class Process(ProcessStatus, AsyncTask):

    def __init__(self, name, command, env=None, stdin=None, stdout=sys.stdout, stderr=sys.stderr):
        ProcessStatus.__init__(self, process_name=name)
        AsyncTask.__init__(self)
        self.name = name
        self.command = command
        self.process = None
        self.process_stop_event = asyncio.Event()

        self.stdout = stdout
        self.stderr = stderr
        if stdin:
            self.stdin = stdin
        else:
            self.stdin = open("/dev/null")

        if env:
            self.env = env
        else:
            self.env = {}

    @asyncio.coroutine
    def start(self):
        if not (self.__status__ == Status.NOTSTARTED or self.__status__ == Status.STOPPED
                or self.__status__ == Status.TERMINATED or self.__status__ == Status.STARTFAILED):
            raise InvalidState(
                "ERROR: Process <%s> is in <%s>. The process can be started only while it in <%s> state" % (
                    self.name, self.__status__.name, "%s, %s, %s or %s" % (
                        Status.NOTSTARTED.name, Status.STOPPED.name, Status.TERMINATED.name,
                        Status.STARTFAILED.name
                    )
                )
            )

        @asyncio.coroutine
        def wait_for_return_code():
            try:
                self.__set_status__(Status.STARTED)
                s = yield from self.process.wait()
                if s != 0:
                    logger.error("Process <%s> terminated "
                          "with non zero return code <%s>." % (self.name, s))
                    if self.__status__ != Status.RESTARTING:
                        self.__set_status__(Status.TERMINATED)
                else:
                    logger.info("Process <%s> stopped." % (
                        self.name))
                    if self.__status__ != Status.RESTARTING:
                        self.__set_status__(Status.STOPPED)
            except Exception as e:
                logger.error("%s" % e)
                logger.error("%s" % traceback.format_exc())
                self.__set_status__(Status.TERMINATED)
            finally:
                self.process_stop_event.set()
                delete_process(self)

        try:
            add_process(self)
            self.__set_status__(Status.STARTING)

            null_device = self.stdin

            self.process_stop_event.clear()
            self.process = yield from asyncio.create_subprocess_exec(
                *self.command, stdin=null_device,
                stdout=self.stdout, stderr=self.stderr,
                env=self.env
            )

            self.new_async_task(wait_for_return_code())

        except Exception as e:
            error = traceback.format_exc()
            logger.error("%s" % e)
            logger.error("%s" % error)
            self.__set_status__(Status.STARTFAILED)


    @asyncio.coroutine
    def wait_for_completion(self):
        while True:
            yield from self.wait_for_async_task_completion()
            if self.__status__ != Status.RESTARTING:
                break
            else:
                while True:
                    yield from asyncio.sleep(2)
                    if self.__status__ != Status.RESTARTING:
                        break


    @asyncio.coroutine
    def restart(self):
        self.__set_status__(Status.RESTARTING)
        try:
            yield from self.stop()
            yield from self.start()
        except InvalidState as e:
            error = traceback.format_exc()
            logger.error("%s" % e)
            logger.error("%s" % error)
            return

    def is_running(self):
        if self.__status__ == Status.STOPPING:
            return True
        if self.__status__ == Status.RESTARTING:
            raise NotRestartedYet("ERROR: %s is restarting" % self.name)
        if self.__status__ == Status.NOTSTARTED:
            raise NotStartedYet("ERROR: %s not started yet" % self.name)
        return self._is_running()

    def _is_running(self):
        if (self.__status__ == Status.NOTSTARTED or self.__status__ == Status.STOPPED
                or self.__status__ == Status.TERMINATED or self.__status__ == Status.STARTFAILED):
            return False
        else:
            return True

    @asyncio.coroutine
    def _is_stopped(self, timeout):
        yield from asyncio.wait_for(self.process_stop_event.wait(), timeout)
        if self._is_running():
            return False
        return True

    @asyncio.coroutine
    def stop(self, timeout=15):
        if self.__status__ == Status.STARTED or self.__status__ == Status.RESTARTING:
            if self.__status__ != Status.RESTARTING:
                self.__set_status__(Status.STOPPING)
            if not self._is_running():
                logger.error("Process <%s> is already stopped."
                      " Ignoring stop request" % self.name)
                return False
            self.process.send_signal(signal.SIGINT)
            stopped = yield from self._is_stopped(timeout)
            if not stopped:
                logger.error("Process <%s> not stopped with SIGINT signal, killing the process" % self.name)
                self.kill()
            return True
        else:
            raise InvalidState(
                "ERROR: Process <%s> is in <%s>. The process can be stopped only while it in <%s or %s> state" % (
                    self.name, self.__status__, Status.STARTED.name, Status.RESTARTING.name
                )
            )

    @asyncio.coroutine
    def terminate(self):
        if self.__status__ == Status.STARTED:
            self.__set_status__(Status.STOPPING)
            if not self._is_running():
                logger.error("Process <%s> is already stopped."
                      " Ignoring stop request" % self.name)
                return False
            self.process.send_signal(signal.SIGTERM)
            yield from self._is_stopped()
            if self._is_running():
                logger.error("Process <%s> not stopped with "
                      "SIGTERM signal, killing the process" % self.name)
                self.kill()
            return True
        else:
            raise InvalidState("ERROR: Process <%s> is in <%s>."
                               " The process can be terminated only while it "
                               "in <%s> state" % (self.name, self.__status__, Status.STARTED))

    @asyncio.coroutine
    def kill(self):
        if not self._is_running():
            logger.error("Process <%s> is already stopped."
                  " Ignoring stop request" % self.name)
            return False
        self.process.send_signal(signal.SIGKILL)
        yield from self._is_stopped()
        if self._is_running():
            logger.error("Process <%s> not stopped with "
                  "SIGKILL signal, may be the process is in <defunct> state" % self.name)
            return False
        return True

    def send_signal(self, sig):
        if not self._is_running():
            logger.error("Process <%s> is already stopped."
                  " Ignoring stop request" % self.name)
            return False
        self.process.send_signal(sig)
        return True


class ProcessGroup(AsyncTask, ProcessStatus):

    def __init__(self, name):
        AsyncTask.__init__(self)
        ProcessStatus.__init__(self, process_name=name)
        self.name = name
        self.processes = {}
        self.status_listener_cb = None

    def add_process(self, name, command, env=None, stdin=None, stdout=sys.stdout, stderr=sys.stderr):
        if name in self.processes:
            raise ValueError("The process with name <%s> is already added to the ProcessGroup<%s>" % (name, self.name))

        def set_process_status(status):
            if name in self.processes:
                self.processes[name]["status"] = status
            else:
                return

            if status in (Status.STOPPED, Status.TERMINATED, Status.STARTFAILED):
                if self.__status__ != Status.STOPPING:
                    logger.warn("Stopping all the process in the ProcessGroup<%s>" % self.name)
                    self.new_async_task(self.stop())
                else:
                    if len([p for p in self.processes.values() if p["status"]
                            not in (Status.STOPPED, Status.TERMINATED, Status.STARTFAILED)]) == 0:
                        self.__set_status__(Status.STOPPED)

            elif self.__status__ == Status.STARTING:
                started = True
                for p in self.processes.values():
                    if p["status"] == Status.STARTING:
                        started = False
                        if self.__status__ != Status.STARTING:
                            self.__set_status__(Status.STARTING)
                        break

                if started:
                    self.__set_status__(Status.STARTED)
            # elif status == Status.STOPPED:

        process = Process(name, command, env, stdin, stdout, stderr)
        process.add_status_listener(set_process_status)
        self.processes[name] = {
            "process": process,
            "status": process.status
        }

        if self.__status__ != Status.NOTSTARTED:
            # TODO: what if the server is currently stopping ?
            self.new_async_task(process.start())

    @asyncio.coroutine
    def remove_process(self, name):
        try:
            process = self.processes[name]["process"]
        except KeyError:
            raise ValueError("The process<%s> is not added to the "
                             "ProcessGroup<%s>" % (name, self.name)) from None

        if self.__status__ == Status.NOTSTARTED:
            del self.processes[name]
        else:
            del self.processes[name]
            yield from process.stop()

    @asyncio.coroutine
    def start(self):
        if self.status not in (Status.NOTSTARTED, Status.STOPPED, Status.TERMINATED, Status.STARTFAILED):
            raise InvalidState(
                "ERROR: ProcessGroup <%s> is in <%s>."
                " The ProcessGroup can be started only while it "
                "in <%s> state" % (
                    self.name, self.__status__.name,
                    "%s, %s, %s or %s" % (
                        Status.NOTSTARTED.name, Status.STOPPED.name, Status.TERMINATED.name,
                        Status.STARTFAILED.name
                    )
                )
            )

        self.__set_status__(Status.STARTING)
        tasks = []
        for p in self.processes.values():
            tasks.append(self.new_async_task(p["process"].start()))

        yield from asyncio.wait(tasks)

    @asyncio.coroutine
    def wait_for_completion(self):
        while True:
            for p in self.processes.values():
                self.new_async_task(p["process"].wait_for_completion())
            yield from self.wait_for_async_task_completion()
            if self.__status__ != Status.RESTARTING:
                break
            else:
                while True:
                    yield from asyncio.sleep(2)
                    if self.__status__ != Status.RESTARTING:
                        break

    @asyncio.coroutine
    def stop(self):
        self.__set_status__(Status.STOPPING)
        tasks = [self.new_async_task(p["process"].stop()) for p in self.processes.values()]

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
        self.__set_status__(Status.RESTARTING)
        try:
            yield from self.stop()
            yield from self.start()
        except InvalidState as e:
            error = traceback.format_exc()
            logger.error("%s" % e)
            logger.error("%s" % error)
            return

    def is_running(self):
        for status in self.processes.values():
            if status in (Status.STARTED, Status.STOPPING, Status.RESTARTING):
                return True

        return False

    def send_signal(self, sig):
        for name, value in self.processes.items():
            value['process'].send_signal(sig)


class NotStartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class NotRestartedYet(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class InvalidState(Exception):
    def __init__(self, msg):
        super().__init__(msg)