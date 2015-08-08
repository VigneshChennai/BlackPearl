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
import virtualenv
import shutil
import os
import functools
import pyinotify
import logging
import logging.handlers

from datetime import datetime
from enum import Enum

from BlackPearl.server.core import process
from BlackPearl.server.core.process import Process, ProcessGroup, AsyncTask, ProcessStatus
from BlackPearl.server import prechecks
from BlackPearl.common import fileutils
from BlackPearl.core import webapps as webapps


logger = logging.getLogger()
ch = logging.StreamHandler()
logger.addHandler(ch)

formatter = logging.Formatter('[%(asctime)s][%(module)s][%(funcName)s][Line: %(levelno)s][%(levelname)s]: %(message)s')
ch.setFormatter(formatter)


@asyncio.coroutine
def analyse_and_pickle_webapps(config, pypath, virtenv_folder, pickle_folder, *app_dirs):
    # Will be used to hold the list of webapp analysis result
    logger.info("Analysing deployed webapps ....")

    webapps_minimal_file = os.path.join(pickle_folder, "webapps.pickle.minimal")
    # Looping over the webapp deployment folders
    for app_dir in app_dirs:
        logger.info("Initializing webapps located at <%s>" % app_dir)

        count = 0
        # Looping over the webapp folders deployed in a deployment folder
        for webapp_folder in webapps.get_webapp_folders(app_dir):
            count += 1
            webapp_virtenv = os.path.join(virtenv_folder, webapp_folder + "_path_" + str(count))
            if not os.access(webapp_virtenv, os.F_OK):
                logger.info("Creating the virtual environment at <%s>. This till take some time." % webapp_virtenv)
                virtualenv.create_environment(webapp_virtenv)
                logger.info("The virtual environment completed successfully.")
            else:
                logger.info("Using the virtual environment at <%s>" % webapp_virtenv)
            # Running the analysing working in a separate process to avoid webapp modules getting imported to main
            # process

            command = [os.path.join(webapp_virtenv, "bin/python"),
                       os.path.join(os.path.dirname(__file__), 'analyzer.py'), webapps_minimal_file,
                       pickle_folder, app_dir, webapp_folder]

            # TODO: The analyse output also goes to server.out. Need to check that how it is happening
            with open(os.path.join(config['path']['log'], "blackpearl", "%s_analysis.out" % webapp_folder), "w") as out:
                p = Process("Process: Webapp <%s> initializer" % app_dir, command, env={
                    "PYTHONPATH": ":".join(
                        [pypath,
                         os.path.join(app_dir, webapp_folder, "src", "api"),
                         os.path.join(app_dir, webapp_folder, "lib"),
                         os.path.join(app_dir, webapp_folder, 'test')]
                    )
                }, stdout=out, stderr=out)
                yield from p.start()
                yield from p.wait_for_completion()

            with open(os.path.join(config['path']['log'], "blackpearl", "%s_analysis.out" % webapp_folder),
                      encoding="UTF-8") as r:
                if p.status == process.Status.STOPPED:
                    logger.info("Webapp<%s> analyse completed successfully." % app_dir)
                    logger.info("Analyse result: %s", r.read())
                else:
                    logger.error(" Webapp<%s> analyse failed." % app_dir)
                    logger.error("Analyse result: %s", r.read())

        logger.info("Webapps deployed at <%s> initialized" % app_dir)

    if os.access(webapps_minimal_file, os.F_OK):
        with open(webapps_minimal_file, "rb") as rb:
            analyse_result_list = pickle.load(rb)
    else:
        analyse_result_list = []

    logger.info("List of initialized webapps : %s" % analyse_result_list)

    # Writing webapp list to file
    da_file = os.path.join(pickle_folder, "deployed_apps.pickle")
    logger.info("Writing deployed apps information to file <%s>." % da_file)
    data = []
    for ret in analyse_result_list:
        data.append({"name": ret.name, "url_prefix": ret.url_prefix})
    with open(da_file, "wb") as da_file:
        pickle.dump(data, da_file)

    return analyse_result_list


def precheck():
    """Function used to perform precheck before starting the application"""
    try:
        prechecks.check_all()
        return True
    except:
        error = traceback.format_exc()
        logger.error(" Error during the precheck.")
        logger.error(" ", error)
        return False


class Uwsgi(ProcessGroup):
    # List of options which can not be overriding from configuration file.
    __immutable_options__ = [
        'socket', 'wsgi-file', 'log-to', 'pidfile', 'touch-workers-reload', 'lazy-apps'
    ]

    def __init__(self, uwsgi_loc, uwsgi_file, webapps_list, logs_dir, run_loc,
                 security_key, security_block_size, nginx_bind, pypath, uwsgi_options, max_log_size, max_log_files):

        super().__init__(name="uWsgi Service")
        self.run_loc = run_loc
        self.uwsgi_loc = uwsgi_loc
        self.webapps_list = []
        self.uwsgi_file = uwsgi_file
        self.logs_dir = logs_dir
        self.security_key = security_key
        self.security_block_size = security_block_size
        self.nginx_bind = nginx_bind
        self.pypath = pypath
        self.uwsgi_options = uwsgi_options

        self._add_apps(webapps_list)
        self.webapps_list = webapps_list

        self.max_log_size = max_log_size
        self.max_log_files = max_log_files

    @asyncio.coroutine
    def add_apps(self, webapps_list):
        deployed_apps_id = [w.id for w in self.webapps_list]
        new_apps_id = [w.id for w in webapps_list]
        logger.debug("Already deployed apps :", deployed_apps_id)
        logger.debug("Apps recently analyzed :", new_apps_id)
        apps_to_start = [webapp for webapp in webapps_list if webapp.id not in deployed_apps_id]
        apps_to_stop = [webapp for webapp in self.webapps_list if webapp.id not in new_apps_id]
        for webapp in apps_to_stop:
            logger.debug("Stopping uWsgi Service for <", webapp.name, "(", webapp.url_prefix,
                         ") > webapp as it is removed or it has error after recent code change")
            yield from self.remove_process("'%s' uWsgi Service" % webapp.id)

        self.webapps_list = webapps_list
        if len(apps_to_start) > 0:
            self.generate_conf_file()
            self._add_apps(apps_to_start)

    def _add_apps(self, apps_to_start):
        for webapp in apps_to_start:
            logger.debug("Starting uWsgi Service for <", webapp.name, "(", webapp.url_prefix, ") > webapp")
            command = [self.uwsgi_loc, '--ini', "%s/uwsgi/%s.conf" % (self.run_loc, webapp.id)]
            self.add_process(
                name="'%s' uWsgi Service" % webapp.id, command=command,
                env={
                    "BLACKPEARL_DEPLOYED_APPS_PICKLE": "%s/uwsgi/pickle/deployed_apps.pickle" % self.run_loc,
                    "BLACKPEARL_PICKLE_FILE": webapp.pickle_file,
                    "BLACKPEARL_ENCRYPT_KEY": self.security_key,
                    "BLACKPEARL_ENCRYPT_BLOCK_SIZE": str(self.security_block_size),
                    "BLACKPEARL_LISTEN": str(self.nginx_bind),
                    "PYTHONPATH": ":".join(
                        [self.pypath,
                         os.path.join(webapp.location, "src", "api"),
                         os.path.join(webapp.location, "lib"),
                         os.path.join(webapp.location, 'test')]
                    )
                }
            )

    def generate_conf_file(self):

        opt = {}
        for key, value in self.uwsgi_options.items():
            if key in Uwsgi.__immutable_options__:
                logger.warn("uWsgi options<%s> can't be overridden. Ignoring .. ")
                continue
            opt[key] = value

        for webapp in self.webapps_list:
            logger.info("Using python at <%s> for webapp<%s>" % (webapp.python_path, webapp.name))
            config = {"socket": webapp.socket, "wsgi-file": self.uwsgi_file,
                      "logto": '%s/uwsgi/%s.log' % (self.logs_dir, webapp.id),
                      "pidfile": '%s/uwsgi/%s.pid' % (self.run_loc, webapp.id), "buffer-size": '32768',
                      "touch-workers-reload": '%s/uwsgi/%s.reload' % (self.run_loc, webapp.id),
                      "workers": str(multiprocessing.cpu_count()), "lazy-apps": 'true',
                      'home': webapp.python_home_path,
                      "touch-logreopen": '%s/uwsgi/%s.log_reopen' % (self.run_loc, webapp.id)}

            config.update(opt)
            conf_list = [str(key) + " = " + str(value) for key, value in config.items()]
            conf_list.insert(0, "[uwsgi]")

            with open("%s/uwsgi/%s.conf" % (self.run_loc, webapp.id), "w") as f:
                f.write("\n".join(conf_list))

    def reload_conf(self):
        self.send_signal(signal.SIGHUP)

    def check_and_rotate_log(self):
        for webapp in self.webapps_list:
            log = '%s/uwsgi/%s.log' % (self.logs_dir, webapp.id)

            rotated = False
            if os.stat(log).st_size > self.max_log_size:
                rotated = True
                if os.access("%s.%s" % (log, self.max_log_files), os.F_OK):
                    os.remove("%s.%s" % (log, self.max_log_files))
                for i in range(self.max_log_files - 1, 0, -1):
                    if os.access("%s.%s" % (log, i), os.F_OK):
                        shutil.move("%s.%s" % (log, i), "%s.%s" % (log, i + 1))

                shutil.move(log, "%s.1" % log)

            if rotated:
                with open('%s/uwsgi/%s.log_reopen' % (self.run_loc, webapp.id), "w") as w:
                    w.write(datetime.now().isoformat())


class Nginx(Process):
    def __init__(self, nginx_loc, hostname, listen,
                 run_loc, share_loc, logs_loc, max_log_size, max_log_files):
        self.nginx_loc = nginx_loc
        self.hostname = hostname
        self.listen = listen
        self.run_loc = run_loc
        self.share_loc = share_loc
        self.logs_loc = logs_loc

        self.max_log_size = max_log_size
        self.max_log_files = max_log_files

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

            def add_value(self, key, *value):
                self.values.append([key, value])

        for webapp in webapps_list:
            location = Location()
            if len(webapp.url_prefix) > 1:
                location.path = '^%s/?$' % webapp.url_prefix
                location.add_value('alias', '%s/src/static/' % webapp.location)
                location.add_value('try_files', 'index.html', '%s/index' % webapp.url_prefix)
                locations.append(location)
                location = Location()
                location.path = '(^%s/(.+))/$' % webapp.url_prefix
                location.add_value('alias', '%s/src/static/$2/' % webapp.location)
                location.add_value('try_files', 'index.html', '$1/index')
                locations.append(location)

                location = Location()
                location.path = '^%s/(.+\.[^/]+$)' % webapp.url_prefix
                location.add_value('alias', '%s/src/static/$1' % webapp.location)
                locations.append(location)
            else:
                location.path = '^/?$'
                location.add_value('alias', '%s/src/static/' % webapp.location)
                location.add_value('try_files', 'index.html', '/index')
                locations.append(location)
                location = Location()
                location.path = '(^/(.+))/$'
                location.add_value('alias', '%s/src/static/$2/' % webapp.location)
                location.add_value('try_files', 'index.html', '$1/index')
                locations.append(location)

                location = Location()
                location.path = '^/(.+\.[^/]+$)'
                location.add_value('alias', '%s/src/static/$1' % webapp.location)
                locations.append(location)

        conf = "\n pid  %s/nginx/nginx.pid;" % self.run_loc
        conf += "\n daemon off;"
        conf += "\n error_log %s/nginx/nginx.error.log  warn;" % self.logs_loc
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

        conf += "\n\n\t server {"
        conf += "\n\t\t listen %s;" % self.listen
        conf += "\n\t\t server_name %s;" % self.hostname
        conf += "\n\t\t access_log %s/nginx/nginx.access.log  main;" % self.logs_loc

        for loc in locations:
            conf += "\n\n\t\t location ~ %s {" % loc.path
            for val in loc.values:
                conf += "\n\t\t\t %s '%s';" % (val[0], "' '".join(val[1]))
            conf += "\n\t\t }"

        for loc in root_location:
            conf += "\n\n\t\t location ~ %s {" % loc.path
            for val in loc.values:
                conf += "\n\t\t\t %s '%s';" % (val[0], "' '".join(val[1]))
            conf += "\n\t\t }"

        for webapp in webapps_list:
            conf += "\n\n\t\t location %s {" % webapp.url_prefix
            conf += "\n\t\t\t uwsgi_pass 'unix://%s';" % webapp.socket
            conf += "\n\t\t\t include '%s/uwsgi_params';" % self.share_loc
            conf += "\n\t\t }"
        conf += "\n\t }"
        conf += "\n }"

        with open("%s/nginx/nginx.conf" % self.run_loc, "w") as f:
            f.write(conf)

    def check_and_rotate_log(self):
        access_log = "%s/nginx/nginx.access.log" % self.logs_loc
        error_log = "%s/nginx/nginx.error.log" % self.logs_loc

        rotated = False
        if os.stat(access_log).st_size > self.max_log_size:
            rotated = True
            if os.access("%s.%s" % (access_log, self.max_log_files), os.F_OK):
                os.remove("%s.%s" % (access_log, self.max_log_files))
            for i in range(self.max_log_files - 1, 0, -1):
                if os.access("%s.%s" % (access_log, i), os.F_OK):
                    shutil.move("%s.%s" % (access_log, i), "%s.%s" % (access_log, i + 1))

            shutil.move(access_log, "%s.1" % access_log)

        if os.stat(error_log).st_size > self.max_log_size:
            rotated = True
            if os.access("%s.%s" % (error_log, self.max_log_files), os.F_OK):
                os.remove("%s.%s" % (error_log, self.max_log_files))
            for i in range(self.max_log_files - 1, 0, -1):
                if os.access("%s.%s" % (error_log, i), os.F_OK):
                    shutil.move("%s.%s" % (error_log, i), "%s.%s" % (error_log, i + 1))

            shutil.move(error_log, "%s.1" % error_log)

        if rotated:
            self.send_signal(signal.SIGUSR1)


Status = Enum("Status", "NOTSTARTED, STARTING, STARTFAILED, STARTED, STOPPING, RESTARTING, STOPPED, TERMINATED")


class AppServer(AsyncTask, ProcessStatus):
    # Instance Variables : config, status, reloading_code, reloading_conf,
    #                      webapp_locations, ev_loop, uwsgi, nginx

    def __init__(self):
        AsyncTask.__init__(self)
        ProcessStatus.__init__(self, process_name="BlackPearl Server")
        self.environment_initialized = False
        self.config = None
        self.reloading_code = False
        self.reloading_conf = False
        self.modified_files = []
        self.webapp_locations = None
        self.ev_loop = None

        self.uwsgi = None
        self.nginx = None

    @asyncio.coroutine
    def initialize_environment(self, config):
        try:
            path = config['path']
            server = config['server']
            hostname = config['hostname']
            listen = config['listen']
            security = config['security']
            uwsgi_options = config['uwsgi_options']

            self.config = config
            self.reloading_code = False
            self.reloading_conf = False
            self.modified_files = []

            webapp_locations = path['webapps']
            self.webapp_locations = webapp_locations

            webapps_list = yield from analyse_and_pickle_webapps(self.config, path['lib'],
                                                                 os.path.join(config['path']['cache'], "virtenv"),
                                                                 "%s/uwsgi/pickle/" % path['run'],
                                                                 *webapp_locations
                                                                 )

            if not webapps_list:
                logger.critical("No application deployed.")
                raise NoApplicationDeployedError("No application deployed")

            for webapp in webapps_list:
                webapp.socket = path['run'] + "/uwsgi/%s.socket" % webapp.id

            # Asyncio the event loop
            self.ev_loop = asyncio.get_event_loop()

            self.uwsgi = Uwsgi(
                server['uwsgi'], path['lib'] + "/wsgi.py", webapps_list,
                path['log'], path['run'], security['key'],
                security['block_size'], listen,
                path['lib'], uwsgi_options, config['logging']['max_log_size'], config['logging']['max_log_files']
            )
            self.uwsgi.generate_conf_file()

            self.nginx = Nginx(
                server['nginx'], hostname, listen,
                path['run'], path['share'], path['log'], config['logging']['max_log_size'],
                config['logging']['max_log_files']
            )
            self.nginx.generate_conf_file(webapps_list)

            # Defining service status change listener
            self.nginx.add_status_listener(functools.partial(self._service_status_update_cb, "nginx "))
            self.uwsgi.add_status_listener(functools.partial(self._service_status_update_cb, "uwsgi"))

        except:
            logger.error("Failed to initialize the environment.")
            logger.error(" %s" % traceback.format_exc())
        else:
            self.environment_initialized = True

    def _init_log_rotation_manager(self):
        @asyncio.coroutine
        def monitor():
            while self.__status__ not in (Status.STOPPED, Status.TERMINATED, Status.STARTFAILED):
                yield from asyncio.sleep(5)
                self.nginx.check_and_rotate_log()
                self.uwsgi.check_and_rotate_log()

        self.new_async_task(monitor())

    def _code_update_monitor_init(self):
        logger.info("Watching <%s> paths for file modifications." % str(self.webapp_locations))
        paths = self.webapp_locations
        excl = pyinotify.ExcludeFilter([al + "/*/src/static" for al in self.webapp_locations])
        self.afm = fileutils.AsyncFileMonitor(self._code_update_cb, loop=self.ev_loop)
        self.afm.set_watch_path(paths, rec=True, exclude_filter=excl)

    def _signal_init(self):
        def signal_handler(signum):
            logger.info('Received signal : %s', signum)
            if signum in (signal.SIGTERM, signal.SIGINT, signal.SIGABRT):
                logger.info("Stopping BlackPearl service")
                self.new_async_task(self.stop())
            elif signum == signal.SIGHUP:
                logger.info("Redeploy BlackPearl")
                self.reload_conf()
            else:
                logger.info("Ignoring signal")

        for signal_name in ('SIGINT', 'SIGTERM', 'SIGABRT', 'SIGHUP'):
            sig = getattr(signal, signal_name)
            self.ev_loop.add_signal_handler(sig, functools.partial(signal_handler, sig))

    @asyncio.coroutine
    def start(self):

        # Initializing Code update Monitor
        self._code_update_monitor_init()

        # Initializing handler for OS signal
        self._signal_init()

        # Initializing log rotation manager
        self._init_log_rotation_manager()

        def start_cb(service, future):
            try:
                future.result()
            except Exception as e:
                error = traceback.format_exc()
                logger.error(" %s" % e)
                logger.error(" %s" % error)
                logger.critical("%s failed to start" % service)

        uwsgi_task = asyncio.async(self.uwsgi.start())
        nginx_task = asyncio.async(self.nginx.start())
        uwsgi_task.add_done_callback(functools.partial(start_cb, "uwsgi"))
        nginx_task.add_done_callback(functools.partial(start_cb, "nginx"))

        yield from asyncio.wait([uwsgi_task, nginx_task])

    @asyncio.coroutine
    def stop(self):
        self.__set_status__(Status.STOPPING)

        def stop_cb(service, future):
            try:
                future.result()
            except Exception as e:
                error = traceback.format_exc()
                logger.error(" %s" % e)
                logger.error(" %s" % error)
                logger.critical("%s failed to stop" % service)

        uwsgi_task = asyncio.async(self.uwsgi.stop())
        nginx_task = asyncio.async(self.nginx.stop())
        uwsgi_task.add_done_callback(functools.partial(stop_cb, "uwsgi"))
        nginx_task.add_done_callback(functools.partial(stop_cb, "nginx"))

        yield from asyncio.wait([uwsgi_task, nginx_task])

    @asyncio.coroutine
    def restart(self):
        self.__set_status__(Status.RESTARTING)

        def restart_cb(service, future):
            try:
                future.result()
            except Exception as e:
                error = traceback.format_exc()
                logger.error(" %s" % e)
                logger.error(" %s" % error)
                logger.critical("%s failed to restart" % service)

        uwsgi_task = asyncio.async(self.uwsgi.restart())
        nginx_task = asyncio.async(self.nginx.restart())
        uwsgi_task.add_done_callback(functools.partial(restart_cb, "uwsgi"))
        nginx_task.add_done_callback(functools.partial(restart_cb, "nginx"))

        yield from asyncio.wait([uwsgi_task, nginx_task])

    @asyncio.coroutine
    def wait_for_completion(self):
        self.new_async_task(self.uwsgi.wait_for_completion())
        self.new_async_task(self.nginx.wait_for_completion())
        yield from self.wait_for_async_task_completion()
        logger.info("BlackPearl service was shutdown")

    def reload_conf(self):
        self.uwsgi.reload_conf()
        self.nginx.reload_conf()

    @asyncio.coroutine
    def reload_code(self):

        if self.reloading_code:
            raise CodeReloadInProgressError("BlackPearl is already reloading the code.")

        try:
            self.reloading_code = True
            yield from asyncio.sleep(2)
            if self.__status__ == Status.STARTED:
                webapps_list = yield from analyse_and_pickle_webapps(
                    self.config['path']['lib'], os.path.join(self.config['path']['cache'], "virtenv"),
                    "%s/uwsgi/pickle/" % self.config['path']['run'],
                    *self.webapp_locations
                )

                self.afm.update_watch_path(rec=True)
                if not webapps_list:
                    logger.warn("Old code retained. Modified code not redeployed.")
                else:
                    modified_webapps = []
                    for webapp in webapps_list:
                        for modified_file in self.modified_files:
                            if modified_file.startswith(webapp.location):
                                modified_webapps.append(webapp)
                    modified_webapps = set(modified_webapps)

                    for webapp in webapps_list:
                        webapp.socket = self.config['path']['run'] + "/uwsgi/%s.socket" % webapp.id

                    self.nginx.generate_conf_file(webapps_list)
                    for m_webapp in modified_webapps:
                        logger.info("Reloading webapp <", m_webapp.name, ">")
                        with open('%s/uwsgi/%s.reload' % (self.uwsgi.run_loc, m_webapp.id), "w") as f:
                            f.write("reload workers")

                    yield from self.uwsgi.add_apps(webapps_list)
                    self.nginx.reload_conf()
                    logger.info("Code updated.")
            else:
                logger.info("Server is in <%s> state. Ignoring restart request." % self.__status__)
        finally:
            self.reloading_code = False

    def _service_status_update_cb(self, service, status):
        other_service = 'uwsgi' if service == "nginx" else "nginx"

        if service == "uwsgi":
            other_status = self.nginx.status
            service_obj = self.uwsgi
            other_service_obj = self.nginx
        else:
            other_status = self.uwsgi.status
            service_obj = self.nginx
            other_service_obj = self.uwsgi

        if status in (process.Status.STOPPED, process.Status.TERMINATED, process.Status.STARTFAILED):

            if other_status not in (process.Status.STOPPED, process.Status.TERMINATED, process.Status.STARTFAILED):
                if self.__status__ != Status.STOPPING:
                    logger.critical("%s service stopped unexpectedly" % service)
                    logger.critical("So, stopping %s service as well" % other_service)
                    self.new_async_task(other_service_obj.stop())
            else:
                if self.__status__ == Status.NOTSTARTED:
                    self.__set_status__(Status.TERMINATED)
                    logger.error(" Failed to startup")

                elif self.__status__ == Status.RESTARTING:
                    self.__set_status__(Status.TERMINATED)
                    logger.info("Service restart failed.")

                elif self.__status__ == Status.STOPPING:
                    self.__set_status__(Status.STOPPED)
                    logger.info("Services stopped.")

                elif self.__status__ == Status.STARTED:
                    self.__set_status__(Status.TERMINATED)
                    logger.error(" Services terminated unexpectedly")
        elif status == process.Status.RESTARTING:
            logger.info("Service <%s> getting restarted." % service)

        elif status == process.Status.STARTED and other_status == process.Status.STARTED:
            logger.info("Service <%s> started up." % service)
            if self.__status__ == Status.RESTARTING:
                self.__set_status__(Status.STARTED)
                logger.info("Services restarted.")
            elif self.__status__ != Status.STARTED:
                self.__set_status__(Status.STARTED)
                logger.info("Services started up")

        elif status == process.Status.STARTED:
            logger.info("Service <%s> started up." % service)

        return True

    def _code_update_cb(self, event):
        if os.path.isdir(event.pathname) or event.pathname.endswith(".py"):
            logger.info("File<%s> modified." % event.pathname)
            self.modified_files.append(event.pathname)
            if not self.reloading_code:
                self.new_async_task(self.reload_code())


def daemonize(log_level, max_log_size, max_log_files, log_folder, wd="/", umask=0):
    try:
        f = os.fork()
    except OSError as e:
        logger.critical("Error forking.. <{fork}>".format(fork=e))
        logger.critical("Trace -> {trace}".format(
            trace=traceback.format_exc()))
        raise e from None

    if f != 0:
        sys.exit(0)
    else:
        signal.signal(signal.SIGHUP, lambda x, y: logger.info("SIGHUP received during process forking, ignoring signal"))
        os.chdir(wd)
        os.setsid()
        os.umask(umask)
        try:
            f = os.fork()
        except OSError as e:
            logger.critical("Error forking.. <{fork}>".format(fork=e))
            logger.critical("Trace -> {trace}".format(
                trace=traceback.format_exc()))
            raise e from None

        if f != 0:
            sys.exit(0)

        logger.info("Started as Daemon")

        _ch = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "blackpearl", "server.log"), mode='a',
                                                  maxBytes=max_log_size, backupCount=max_log_files,
                                                  encoding="UTF-8", delay=0)
        ch.setLevel(log_level)
        logger.addHandler(_ch)

        r = open("/dev/null", "r")
        os.dup2(r.fileno(), 0)
        buffering = 1  # line buffering
        w = open(os.path.join(log_folder, "blackpearl", "server.out"), "w", buffering=buffering)
        os.dup2(w.fileno(), 1)
        os.dup2(w.fileno(), 2)


def start(config, daemon=False):
    print("Performing prechecks .... ", end="")

    ch.setLevel(config['logging']['level'])
    logger.setLevel(config['logging']['level'])

    path = config['path']
    try:
        prechecks.check_all()
    except Exception as e:
        print("[Failed]")
        logger.critical("%s" % str(e))
        logger.info("BlackPearl server not started ....")
        sys.exit(-1)
    else:
        print("[Ok]")
        if daemon:
            logger.info("Starting BlackPearl in daemon mode ...")
            try:
                daemonize(config['logging']['level'], config['logging']['max_log_size'],
                          config['logging']['max_log_files'], log_folder=path['log'])
            except OSError:
                logger.error(traceback.format_exc())
                logger.error("Unable to start the server in daemon mode. Exiting.")
                sys.exit(1)

        # Writing BlackPearl PID to file
        with open(path['run'] + "/BlackPearl.pid", "w") as f:
            f.write(str(os.getpid()))

        ev_loop = asyncio.get_event_loop()
        app_server = AppServer()

        initialize_task = asyncio.async(app_server.initialize_environment(config))

        # Waits till server starts
        ev_loop.run_until_complete(initialize_task)

        if app_server.environment_initialized:
            start_task = asyncio.async(app_server.start())

            # Waits till server starts
            ev_loop.run_until_complete(start_task)
            logger.info("BlackPearl services started.")

            try:
                # Waiting for server to shutdown
                ev_loop.run_until_complete(app_server.wait_for_completion())
            finally:
                ev_loop.close()
        else:
            logger.error(" BlackPearl services not started due to the issue occurred during environment initialization.")
            ev_loop.close()


class NoApplicationDeployedError(Exception):
    pass


class CodeReloadInProgressError(Exception):
    pass


class ConfReloadInProgressError(Exception):
    pass
