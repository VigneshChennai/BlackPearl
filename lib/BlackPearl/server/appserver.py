#!/usr/bin/env python

#This file is part of BlackPearl.

#BlackPearl is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#BlackPearl is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import threading
import subprocess
import traceback
import time
import sys
import signal
import pyinotify
import asyncio
import functools
import multiprocessing
import pickle

from BlackPearl.server.core.process import Process, NotStartedYet, NotRestartedYet, InvalidState
from BlackPearl.server.utils import prechecks, fileutils
from BlackPearl.server.core.logger import Logger
from BlackPearl.server import config
from BlackPearl.core import webapps as Webapps


class WebAppMinimal:
    def __init__(self, location, url_prefix):
        self.location = location
        self.url_prefix = url_prefix

def analyse_and_pickle_webapps(picklefile, *appdirs):

    def analyser(queue):
        try:
            webapps = []
            for appdir in appdirs:
                print("INFO: Analysing deployed webapps ....")
                webapps.extend(Webapps.initialize(appdir))
            print("INFO: Webapps analysing completed.")
            print("INF0: Writing analysed information to <%s>" % picklefile)
            with open(picklefile, "wb") as pfile:
                pickle.dump(webapps, pfile)
            print("INFO: Write completed")
            _webapps = []
            for webapp in webapps:
                _webapps.append(
                    WebAppMinimal(webapp.location, webapp.url_prefix))
            queue.put(_webapps)
        except:
            print("ERROR: Fatal error during analysing webapps.")
            print("ERROR: %s" %traceback.format_exc())
            queue.put(None)

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=analyser, args=(q,))
    p.start()
    ret = q.get()
    p.join()

    return ret

def precheck():
    try:
        prechecks.check_all()
        return True
    except:
        return False

class Uwsgi(Process):

    def __init__(self, uwsgi_loc, temp_loc, uwsgi_file, socket_file, logs_dir):

        self.temp_loc = temp_loc
        self.uwsgi_loc = uwsgi_loc
        self.uwsgi_sock = socket_file
        self.uwsgi_file = uwsgi_file
        self.logs_dir = logs_dir

        command =[self.uwsgi_loc, '--plugins', 'python',
                '--socket', self.uwsgi_sock,
                '--wsgi-file', self.uwsgi_file,
                '--enable-threads', '--logto',
                '%s/uwsgi.log' % (self.logs_dir),
                '--pidfile', '%s/uwsgi.pid' % (self.temp_loc),
                '--buffer-size=32768',
                '--touch-workers-reload', '%s/uwsgi_worker_reload.file' % (self.temp_loc),
                '--workers', str(multiprocessing.cpu_count()),
                '--lazy-apps']

        try:
            virtenv = os.environ['VIRTUAL_ENV']
            print("INFO: Using python at <%s> for uwsgi service" % virtenv)
            command.append('--home')
            command.append(virtenv)
        except:
            print("INFO: Using system installed python for uwsgi service")

        super().__init__(name = "uWsgi Service", command=command,
                        env={
                            "BLACKPEARL_TMP" : config.temp,
                            "BLACKPEARL_ENCRYPT_KEY" : str(config.security_key),
                            "BLACKPEARL_ENCRYPT_BLOCK_SIZE" : str(config.security_block_size),
                            "BLACKPEARL_LISTEN" : str(config.listen),
                            "PYTHONPATH" :  ":".join([
                                                   config.lib,
                                                   config.webapps,
                                                   config.adminapps,
                                                   config.defaultapps
                                             ])
                        })

    def reload_conf(self):
        self.send_signal(signal.SIGHUP)

class Nginx(Process):

    def __init__(self, hostname, listen, socket, webapps_loc,
                       temp_loc, share_loc, logs_loc):
        self.hostname = hostname
        self.listen = listen
        self.socket = socket
        self.webapps_loc = webapps_loc
        self.temp_loc = temp_loc
        self.share_loc = share_loc
        self.logs_loc = logs_loc

        command =[config.nginx, '-c', '{tmp}/nginx.conf'.format(tmp=self.temp_loc)]

        super().__init__(name = "Nginx Service", command = command)

    def reload_conf(self):
        self.send_signal(signal.SIGHUP)

    def generate_conf_file(self, webapps):
        locations = []
        root_location = []
        class Location:

            def __init__(self):
                self.path = None
                self.values = []

            def add_value(self, key, value):
                self.values.append([key, value])

        for webapp in webapps:
            location = Location()
            if len(webapp.url_prefix) > 0:
                location.path = '/%s/(.+\..+)' % (webapp.url_prefix)
                location.add_value('alias', '%s/static/$1' % (
                                        webapp.location))
                locations.append(location)
                location = Location()
                location.path = '/%s(.*/$)' % (webapp.url_prefix)
                location.add_value('alias', '%s/static$1' % (
                                        webapp.location))
                locations.append(location)
            else:
                location.path = '/(.+\..+)'
                location.add_value('alias', '%s/static/$1' % (
                                        webapp.location))
                root_location.append(location)
                location = Location()
                location.path = '(/$)'
                location.add_value('alias', '%s/static$1' % (
                                        webapp.location))
                root_location.append(location)

        conf = "\npid  %s/nginx.pid;" % (self.temp_loc)
        conf += "\ndaemon off;"
        conf += "\nworker_processes %s;" % str(multiprocessing.cpu_count())
        conf += "\n\nevents {"
        conf += "\n\tworker_connections  1024;"
        conf += "\n}"

        conf += "\n\nhttp {"
        conf += "\n\tinclude      '%s/mime.types';" % (self.share_loc)
        conf += "\n\tdefault_type  application/octet-stream;"
        conf += "\n\tsendfile        on;"
        conf += "\n\tkeepalive_timeout  65;"
        conf += "\n\tclient_body_temp_path  /tmp/cache 1 2;"
        conf += """\n\tlog_format  main  '$remote_addr - $remote_user """
        conf += """[$time_local] "$request" '"""
        conf += """\n\t'$status $body_bytes_sent "$http_referer" '"""
        conf += """\n\t'"$http_user_agent" "$http_x_forwarded_for"';"""
        conf += "\n\terror_log %s/nginx.error.log  warn;" % (
                            self.logs_loc)
        conf += "\n\n\tupstream BlackPearl {"
        conf += "\n\t\tserver unix://%s;" % (self.socket)
        conf += "\n\t}"

        conf += "\n\n\tserver {"
        conf += "\n\t\tlisten %s;" % (self.listen)
        conf += "\n\t\tserver_name %s;" %(self.hostname)
        conf += "\n\t\troot '%s';" % (self.webapps_loc)
        conf += "\n\t\taccess_log %s/nginx.access.log  main;" % (
                            self.logs_loc)

        for loc in locations:
            conf += "\n\n\t\tlocation ~ %s {" % (loc.path)
            for val in loc.values:
                conf += "\n\t\t\t%s '%s';" % (val[0], val[1])
            conf += "\n\t\t}"

        for loc in root_location:
            conf += "\n\n\t\tlocation ~ %s {" % (loc.path)
            for val in loc.values:
                conf += "\n\t\t\t%s '%s';" % (val[0], val[1])
            conf += "\n\t\t}"

        conf += "\n\n\t\tlocation / {"
        conf += "\n\t\t\tuwsgi_pass BlackPearl;"
        conf += "\n\t\t\tinclude '%s/uwsgi_params';" % (self.share_loc)
        conf += "\n\t\t}"
        conf += "\n\t}"
        conf += "\n}"

        with open("%s/nginx.conf" % (self.temp_loc), "w") as f:
            f.write(conf)



class AppServer():

    def __init__(self, options, webapps):
        self.uwsgi = Uwsgi(options['uwsgi'],
                           options['temp'],
                           options['home'] + "/lib/wsgi.py",
                           options['temp'] + "/wsgi.sock",
                           options['logs'])

        self.nginx = Nginx(options['hostname'],
                           options['listen'],
                           options['temp'] + "/wsgi.sock",
                           options['webapps'],
                           options['temp'],
                           options['share'],
                           options['logs'])
        self.nginx.generate_conf_file(webapps)
        self.status = "NOTSTARTED"

    def _start_uwsgi_cb(self, future):
        try:
            future.result()
        except Exception as e:
            error = traceback.format_exc()
            print("ERROR: %s" % (e))
            print("ERROR: %s" % (error))
            print("SEVERE: uwsgi failed to start")

    def _start_nginx_cb(self, future):
        try:
            future.result()
        except Exception as e:
            error = traceback.format_exc()
            print("ERROR: %s" % (e))
            print("ERROR: %s" % (error))
            print("SEVERE: Nginx failed to start")

    def start(self):
        uwsgi_task = asyncio.async(self.uwsgi.start())
        uwsgi_task.add_done_callback(self._start_uwsgi_cb)
        nginx_task = asyncio.async(self.nginx.start())
        nginx_task.add_done_callback(self._start_nginx_cb)

    def _stop_uwsgi_cb(self, nginx_task, future):
        try:
            future.result()
        except:
            print("SEVERE: uwsgi failed to stop")
        nginx_task.add_done_callback(self._stop_nginx_cb)

    def _stop_nginx_cb(self, future):
        try:
            future.result()
        except:
            print("SEVERE: Nginx failed to stop")

        self.status = "STOPPED"

    def stop(self):
        self.status = "STOPPING"
        uwsgi_task = asyncio.async(self.uwsgi.stop())
        nginx_task = asyncio.async(self.nginx.stop())
        uwsgi_task.add_done_callback(
            functools.partial(self._stop_uwsgi_cb, nginx_task))


    def code_updated(self, webapps):
        print("INFO: Code updated.")
        self.nginx.generate_conf_file(webapps)
        with open('%s/uwsgi_worker_reload.file' % (self.uwsgi.temp_loc), "w") as f:
            f.write("reload workers")
        self.nginx.reload_conf()

    def reload_conf(self):
        self.uwsgi.reload_conf()
        self.nginx.reload_conf()

    def restart(self):
        self.status = "RESTARTING"
        asyncio.async(self.uwsgi.restart())
        asyncio.async(self.nginx.restart())

    @asyncio.coroutine
    def monitor(self):
        while True:
            try:
                started = self.isrunning()
            except NotStartedYet:
                print("INFO: Waiting for service to startup")
                yield from asyncio.sleep(2)
            else:
                if started:
                    print("INFO: Services started up")
                    self.status = "STARTED"
                else:
                    print("ERROR: Failed to startup")
                    self.status = "TERMINATED"
                break

        while True:
            try:
                if not self.isrunning() and self.status != "STOPPING":
                    print("INFO: Services stopped.")
                    break
            except NotRestartedYet:
                print("INFO: Services restarting.")
                while True:
                    yield from asyncio.sleep(2)
                    try:
                        if self.isrunning():
                            self.status = "STARTED"
                            print("INFO: Service restarted.")
                            break
                        else:
                            self.status = "TERMINATED"
                            print("INFO: Service restart failed.")
                    except NotRestartedYet:
                        print("INFO: Not restarted yet.")
                        pass

            yield from asyncio.sleep(2)
        print("INFO: BlackPearl services stopped")

    def isrunning(self):
        if self.uwsgi.isrunning() and self.nginx.isrunning():
            return True
        elif not self.uwsgi.isrunning() and not self.nginx.isrunning():
            return False
        else:
            if self.status != "STOPPING":
                if self.uwsgi.isrunning():
                    print("SEVERE: Nginx service stopped unexpectedly")
                    print("SEVERE: So, stopping uWsgi service as well")
                    asyncio.async(self.uwsgi.stop())
                elif self.nginx.isrunning():
                    print("SEVERE: uWsgi service stopped unexpectedly")
                    print("SEVERE: So, stopping Nginx service as well")
                    asyncio.async(self.nginx.stop())

            return True

def start(daemon=False):
    print("Performing precheck .... ", end="")
    if not precheck():
        print("[Failed]\nNode not started ....")
        sys.exit(-1)
    else:
        print("[Ok]")
        if daemon:
            try:
                f = os.fork()
            except OSError as e:
                print("SEVERE: Error forking.. <{fork}>".format(fork=e))
                print("SEVERE: Trace -> {trace}".format(
                                             trace=traceback.format_exc()))
            if f != 0:
                print("\nINFO: BlackPearl server is invoked to start as daemon\n")
                sys.exit(0)
            else:
                signal.signal(signal.SIGHUP,
                            lambda x,y: print("SIGHUP received during process"\
                                              " forking, ignoring signal"))
                os.chdir("/")
                os.setsid()
                os.umask(0)
                try:
                    f = os.fork()
                except OSError as e:
                    print("SEVERE: Error forking.. <{fork}>".format(fork=e))
                    print("SEVERE: Trace -> {trace}".format(
                                             trace=traceback.format_exc()))
                    sys.exit(0)
                if f != 0:
                    sys.exit(0)

                r = open("/dev/null", "r")
                os.dup2(r.fileno(), 0)
                buffering=1 #line buffering
                w = open(config.logs + "/server.log", "w",
                            buffering=buffering)
                os.dup2(w.fileno(), 1)
                os.dup2(w.fileno(), 2)
                print("INFO: Starting BlackPearl in daemon mode ...")

        logger = Logger(Logger.INFO)
        logger.initialize()
        with open(config.temp + "/BlackPearl.pid", "w") as f:
            f.write(str(os.getpid()))

        webapps = analyse_and_pickle_webapps("%s/pickle/webapps" % config.temp,
                                             config.defaultapps,
                                             config.webapps
                                            )
        if webapps == None:
            print("SEVERE: No application deployed.")
            sys.exit(1)

        paths = [
                config.defaultapps,
                config.webapps
                ]
        excl = pyinotify.ExcludeFilter([
                config.defaultapps + "/*/static",
                config.webapps + "/*/static"
                ])

        evloop = asyncio.get_event_loop()

        options = {}
        for option in config._options:
            options[option] = config.__dict__[option]

        appserver = AppServer(options, webapps)

        evloop.call_soon(appserver.start)

        def reload_code():
            try:
                running = appserver.isrunning()
            except NotStartedYet:
                pass
            except NotRestartedYet:
                pass
            else:
                if running:
                    webapps = analyse_and_pickle_webapps(
                                            "%s/pickle/webapps" % config.temp,
                                             config.defaultapps,
                                             config.webapps
                                            )
                    if webapps == None:
                        print("WARNING: Old code retained."\
                              " Modified code not redeployed.")
                    else:
                        appserver.code_updated(webapps)
            reload_code.called = False

        reload_code.called = False

        def filemodified_callback(event):
            if event.pathname.endswith(".py"):
                print("INFO: File<%s> modified." % (event.pathname))
                if not reload_code.called:
                    reload_code.called = True
                    evloop.call_later(1, reload_code)

        afm = fileutils.AsyncFileMonitor(filemodified_callback)
        afm.add_watch_path(paths, rec=True, exclude_filter=excl)


        def signal_handler(signum):
            print('Receive signal : ', signum)
            if signum in (signal.SIGTERM, signal.SIGINT, signal.SIGABRT):
                print("INFO: Stopping BlackPearl service")
                appserver.stop()
            elif signum == signal.SIGHUP:
                print("INFO: Redeploy BlackPearl")
                appserver.reload_conf()
            else:
                print("INFO: Ignoring signal")

        for signame in ('SIGINT', 'SIGTERM', 'SIGABRT', 'SIGHUP'):
            SIG = getattr(signal, signame)
            evloop.add_signal_handler(SIG,
                                    functools.partial(signal_handler, SIG))

        evloop.run_until_complete(appserver.monitor())

