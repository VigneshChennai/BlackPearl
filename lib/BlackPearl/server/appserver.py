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

import traceback
import sys
import signal
import asyncio
import multiprocessing
import pickle
import os
import functools

import pyinotify

from BlackPearl.server.core.process import Process, NotStartedYet, NotRestartedYet
from BlackPearl.server.utils import prechecks, fileutils
from BlackPearl.server.core.logger import Logger
from BlackPearl.core import webapps as webapps


class WebAppMinimal:
    def __init__(self, location, url_prefix):
        self.location = location
        self.url_prefix = url_prefix


def analyse_and_pickle_webapps(picklefile, *appdirs):
    def analyser(queue):
        try:
            webapps_list = []
            print("INFO: Analysing deployed webapps ....")
            for appdir in appdirs:
                temp = webapps.initialize(appdir)
                if temp:
                    webapps_list.extend(temp)
            print("INFO: Webapps analysing completed.")
            print("INF0: Writing analysed information to <%s>" % picklefile)
            with open(picklefile, "wb") as pfile:
                pickle.dump(webapps_list, pfile)
            print("INFO: Write completed")
            _webapps = []
            for webapp in webapps_list:
                _webapps.append(
                    WebAppMinimal(webapp.location, webapp.url_prefix))
            queue.put(_webapps)
        except:
            print("ERROR: Fatal error during analysing webapps.")
            print("ERROR: %s" % traceback.format_exc())
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
    __immutable_options__ = [
        'socket', 'wsgi-file', 'log-to', 'pidfile', 'touch-workers-reload', 'lazy-apps'
    ]

    def __init__(self, uwsgi_loc, uwsgi_file, socket_file, logs_dir, run_loc,
                 security_key, security_block_size, nginx_bind, pypath, uwsgi_options):

        self.run_loc = run_loc
        self.uwsgi_loc = uwsgi_loc
        self.uwsgi_sock = socket_file
        self.uwsgi_file = uwsgi_file
        self.logs_dir = logs_dir
        self.security_key = security_key
        self.security_block_size = security_block_size
        self.nginx_bind = nginx_bind
        self.pypath = pypath
        self.uwsgi_options = uwsgi_options

        command = [self.uwsgi_loc, '--ini', "%s/uwsgi/uwsgi.conf" % self.run_loc]

        super().__init__(name="uWsgi Service", command=command,
                         env={
                             "BLACKPEARL_RUN": self.run_loc,
                             "BLACKPEARL_ENCRYPT_KEY": self.security_key,
                             "BLACKPEARL_ENCRYPT_BLOCK_SIZE": str(self.security_block_size),
                             "BLACKPEARL_LISTEN": str(self.nginx_bind),
                             "PYTHONPATH": ":".join(self.pypath)
                         })

    def generate_conf_file(self):
        config = {
            "socket": self.uwsgi_sock,
            "wsgi-file": self.uwsgi_file,
            "logto": '%s/uwsgi.log' % self.logs_dir,
            "pidfile": '%s/uwsgi/uwsgi.pid' % self.run_loc,
            "buffer-size": '32768',
            "touch-workers-reload": '%s/uwsgi/worker_reload.file' % self.run_loc,
            "workers": str(multiprocessing.cpu_count()),
            "lazy-apps": 'true'
        }
        try:
            virtenv = os.environ['VIRTUAL_ENV']
            print("INFO: Using python at <%s> for uwsgi service" % virtenv)
            config['home'] = virtenv
        except:
            print("INFO: Using system installed python for uwsgi service")

        for key, value in self.uwsgi_options.items():
            if key in Uwsgi.__immutable_options__:
                print("WARNING: uWsgi options<%s> can't be overridden. Ignoring .. ")
                continue
            config[key] = value

        conf_list = [str(key) + " = " + str(value) for key, value in config.items()]
        conf_list.insert(0, "[uwsgi]")

        with open("%s/uwsgi/uwsgi.conf" % self.run_loc, "w") as f:
            f.write("\n".join(conf_list))

    def reload_conf(self):
        self.send_signal(signal.SIGHUP)


class Nginx(Process):
    def __init__(self, nginx_loc, hostname, listen, socket, webapps_loc,
                 run_loc, share_loc, logs_loc):
        self.nginx_loc = nginx_loc
        self.hostname = hostname
        self.listen = listen
        self.socket = socket
        self.webapps_loc = webapps_loc
        self.run_loc = run_loc
        self.share_loc = share_loc
        self.logs_loc = logs_loc

        command = [self.nginx_loc, '-c', '{run}/nginx/nginx.conf'.format(run=self.run_loc)]

        super().__init__(name="Nginx Service", command=command)

    def reload_conf(self):
        self.send_signal(signal.SIGHUP)

    def generate_conf_file(self, webapps_list):
        locations = []
        root_location = []

        class Location:

            def __init__(self):
                self.path = None
                self.values = []

            def add_value(self, key, value):
                self.values.append([key, value])

        for webapp in webapps_list:
            location = Location()
            if len(webapp.url_prefix) > 1:
                location.path = '%s/(.+\..+)' % webapp.url_prefix
                location.add_value('alias', '%s/static/$1' % (
                    webapp.location))
                locations.append(location)
                location = Location()
                location.path = '%s(.*/$)' % webapp.url_prefix
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

        conf = "\n pid  %s/nginx/nginx.pid;" % self.run_loc
        conf += "\n daemon off;"
        conf += "\n error_log %s/nginx.error.log  warn;" % self.logs_loc
        conf += "\n worker_processes %s;" % str(multiprocessing.cpu_count())
        conf += "\n\n events {"
        conf += "\n\t worker_connections  1024;"
        conf += "\n }"

        conf += "\n\n http {"
        conf += "\n\t include      '%s/mime.types';" % self.share_loc
        conf += "\n\t default_type  application/octet-stream;"
        conf += "\n\t sendfile        on;"
        conf += "\n\t keepalive_timeout  65;"
        conf += "\n\t client_body_temp_path  %s/nginx/cache 1 2;" % self.run_loc
        conf += "\n\t proxy_temp_path %s/nginx/proxy;" % self.run_loc
        conf += "\n\t fastcgi_temp_path %s/nginx/fastcgi;" % self.run_loc
        conf += "\n\t scgi_temp_path %s/nginx/scgi;" % self.run_loc
        conf += "\n\t uwsgi_temp_path %s/nginx/uwsgi;" % self.run_loc
        conf += """\n\t log_format  main  '$remote_addr - $remote_user """
        conf += """ [$time_local] "$request" '"""
        conf += """\n\t '$status $body_bytes_sent "$http_referer" '"""
        conf += """\n\t '"$http_user_agent" "$http_x_forwarded_for"';"""
        conf += "\n\n\t upstream BlackPearl {"
        conf += "\n\t\t server unix://%s;" % self.socket
        conf += "\n\t }"

        conf += "\n\n\t server {"
        conf += "\n\t\t listen %s;" % self.listen
        conf += "\n\t\t server_name %s;" % self.hostname
        conf += "\n\t\t root '%s';" % self.webapps_loc
        conf += "\n\t\t access_log %s/nginx.access.log  main;" % self.logs_loc

        for loc in locations:
            conf += "\n\n\t\t location ~ %s {" % loc.path
            for val in loc.values:
                conf += "\n\t\t\t %s '%s';" % (val[0], val[1])
            conf += "\n\t\t }"

        for loc in root_location:
            conf += "\n\n\t\t location ~ %s {" % loc.path
            for val in loc.values:
                conf += "\n\t\t\t %s '%s';" % (val[0], val[1])
            conf += "\n\t\t }"

        conf += "\n\n\t\t location / {"
        conf += "\n\t\t\t uwsgi_pass BlackPearl;"
        conf += "\n\t\t\t include '%s/uwsgi_params';" % self.share_loc
        conf += "\n\t\t }"
        conf += "\n\t }"
        conf += "\n }"

        with open("%s/nginx/nginx.conf" % self.run_loc, "w") as f:
            f.write(conf)


class AppServer():
    def __init__(self, config, webapps_list):
        self.config = config
        app_loc = [config.webapps]

        if config.adminapps_enabled:
            app_loc.append(config.adminapps)

        if config.builtinapps_enabled:
            app_loc.append(config.builtinapps)

        self.app_loc = app_loc
        self.uwsgi = Uwsgi(
            config.uwsgi, config.home + "/lib/wsgi.py", config.run + "/uwsgi/uwsgi.sock",
            config.logs, config.run, config.security_key, config.security_block_size, config.listen,
            [config.lib] + app_loc, config.uwsgi_options
        )
        self.uwsgi.generate_conf_file()

        self.nginx = Nginx(
            config.nginx, config.hostname, config.listen, self.uwsgi.uwsgi_sock, config.webapps,
            config.run, config.share, config.logs
        )
        self.nginx.generate_conf_file(webapps_list)
        self.status = "NOTSTARTED"
        self.reload_code_called = False
        self.afm = None

        self._uwsgi_status = "NOTSTARTED"
        self._nginx_status = "NOTSTARTED"

        self.nginx.add_status_listener(functools.partial(self._status_modified_cb, "nginx"))
        self.uwsgi.add_status_listener(functools.partial(self._status_modified_cb, "uwsgi"))

        # Initializing Code update Monitor
        print("INFO: Watching <%s> paths for file modifications." % str(self.app_loc))
        paths = self.app_loc
        excl = pyinotify.ExcludeFilter([al + "/*/static" for al in self.app_loc])
        self.afm = fileutils.AsyncFileMonitor(self._code_modified_cb)
        self.afm.set_watch_path(paths, rec=True, exclude_filter=excl)

    def start(self):

        def start_cb(service, future):
            try:
                future.result()
            except Exception as e:
                error = traceback.format_exc()
                print("ERROR: %s" % e)
                print("ERROR: %s" % error)
                print("SEVERE: %s failed to start" % service)

        asyncio.async(self.uwsgi.start()).add_done_callback(functools.partial(start_cb, "uwsgi"))
        asyncio.async(self.nginx.start()).add_done_callback(functools.partial(start_cb, "nginx"))

    def stop(self):
        self.status = "STOPPING"

        def start_cb(service, future):
            try:
                future.result()
            except Exception as e:
                error = traceback.format_exc()
                print("ERROR: %s" % e)
                print("ERROR: %s" % error)
                print("SEVERE: %s failed to stop" % service)

        asyncio.async(self.uwsgi.stop()).add_done_callback(functools.partial(start_cb, "uwsgi"))
        asyncio.async(self.nginx.stop()).add_done_callback(functools.partial(start_cb, "nginx"))

    def reload_conf(self):
        self.uwsgi.reload_conf()
        self.nginx.reload_conf()

    def reload_code(self):
        if self.status == "STARTED":
            webapps_list = analyse_and_pickle_webapps(
                "%s/uwsgi/pickle/webapps" % self.config.run,
                *self.app_loc
            )
            self.afm.update_watch_path(rec=True)
            if not webapps_list:
                print("WARNING: Old code retained."
                      " Modified code not redeployed.")
            else:
                print("INFO: Code updated.")
                self.nginx.generate_conf_file(webapps_list)
                with open('%s/uwsgi/worker_reload.file' % self.uwsgi.run_loc, "w") as f:
                    f.write("reload workers")
                self.nginx.reload_conf()
        else:
            print("INFO: Server is in <%s> state. Ignoring restart request." % self.status)

        self.reload_code_called = False

    def restart(self):
        self.status = "RESTARTING"
        asyncio.async(self.uwsgi.restart())
        asyncio.async(self.nginx.restart())

    def _status_modified_cb(self, service, status):
        other_service = 'uwsgi' if service == "nginx" else "nginx"

        if service == "uwsgi":
            self._uwsgi_status = status
            other_status = self._nginx_status
            service_obj = self.uwsgi
            other_service_obj = self.nginx
        else:
            self._nginx_status = status
            other_status = self._uwsgi_status
            service_obj = self.nginx
            other_service_obj = self.uwsgi

        if status in ("STOPPED", "TERMINATED"):

            if other_status not in ("STOPPED", "TERMINATED"):
                if self.status != 'STOPPING':
                    print("SEVERE: %s service stopped unexpectedly" % service)
                    print("SEVERE: So, stopping %s service as well" % other_service)
                    asyncio.async(other_service_obj.stop())
            else:
                if self.status == "NOTSTARTED":
                    self.status = "TERMINATED"
                    print("ERROR: Failed to startup")
                    asyncio.get_event_loop().stop()

                elif self.status == "RESTARTING":
                    self.status = "TERMINATED"
                    print("INFO: Service restart failed.")
                    asyncio.get_event_loop().stop()

                elif self.status == "STOPPING":
                    self.status = "STOPPED"
                    print("INFO: Services stopped.")
                    asyncio.get_event_loop().stop()

        elif status == "RESTARTING":
            print("INFO: Service <%s> getting restarted." % service)

        elif status == "STARTED" and other_status == "STARTED":
            print("INFO: Service <%s> started up." % service)
            if self.status == "RESTARTING":
                self.status = "STARTED"
                print("INFO: Services restarted.")
            elif self.status != "STARTED":
                self.status = "STARTED"
                print("INFO: Services started up")

        elif status == "STARTED":
            print("INFO: Service <%s> started up." % service)

        return True

    def _code_modified_cb(self, event):
        if os.path.isdir(event.pathname) or event.pathname.endswith(".py"):
            print("INFO: File<%s> modified." % event.pathname)
            if not self.reload_code_called:
                self.reload_code_called = True
                ev_loop = asyncio.get_event_loop()
                ev_loop.call_later(1, self.reload_code)


def start(config, daemon=False):
    print("Performing precheck .... ", end="")
    try:
        prechecks.check_all()
    except Exception as e:
        print("[Failed]")
        print("SEVERE: %s" % str(e))
        print("BlackPearl server not started ....")

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
                sys.exit(1)

            if f != 0:
                print("\nINFO: BlackPearl server is invoked to start as daemon\n")
                sys.exit(0)
            else:
                signal.signal(signal.SIGHUP,
                              lambda x, y: print("SIGHUP received during process"
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
                buffering = 1  # line buffering
                w = open(config.logs + "/server.log", "w",
                         buffering=buffering)
                os.dup2(w.fileno(), 1)
                os.dup2(w.fileno(), 2)
                print("INFO: Starting BlackPearl in daemon mode ...")

        logger = Logger(Logger.INFO)
        logger.initialize()
        with open(config.run + "/BlackPearl.pid", "w") as f:
            f.write(str(os.getpid()))

        app_loc = [config.webapps]

        if config.adminapps_enabled:
            app_loc.append(config.adminapps)

        if config.builtinapps_enabled:
            app_loc.append(config.builtinapps)

        webapps_list = analyse_and_pickle_webapps(
            "%s/uwsgi/pickle/webapps" % config.run,
            *app_loc
        )
        if not webapps_list:
            print("SEVERE: No application deployed.")
            sys.exit(1)

        ev_loop = asyncio.get_event_loop()

        app_server = AppServer(config, webapps_list)

        ev_loop.call_soon(app_server.start)

        def signal_handler(signum):
            print('Received signal : ', signum)
            if signum in (signal.SIGTERM, signal.SIGINT, signal.SIGABRT):
                print("INFO: Stopping BlackPearl service")
                app_server.stop()
            elif signum == signal.SIGHUP:
                print("INFO: Redeploy BlackPearl")
                app_server.reload_conf()
            else:
                print("INFO: Ignoring signal")

        for signame in ('SIGINT', 'SIGTERM', 'SIGABRT', 'SIGHUP'):
            sig = getattr(signal, signame)
            ev_loop.add_signal_handler(sig, functools.partial(signal_handler, sig))

        try:
            ev_loop.run_forever()
        except:
            ev_loop.close()