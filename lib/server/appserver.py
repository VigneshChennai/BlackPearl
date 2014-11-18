#!/usr/bin/env python

import os
import re
import threading
import subprocess
import traceback
import time
import sys
import signal

from darkchoco.core import webapps as Webapps
from server.core.process import Process
from server.utils import prechecks
from server.exceptions import NotStartedYet

from server.logger import Logger

def precheck():
    try:
        prechecks.check_all()
        return True
    except:
        return False
        
class Uwsgi(Process):
    
    def __init__(self, conf):
        self.app_loc = conf['DARKCHOCO_APPS']
        self.temp_loc = conf['DARKCHOCO_TMP']
        self.share_loc = conf['DARKCHOCO_SHARE']
        self.log_loc = conf['DARKCHOCO_LOGS']
        self.uwsgi_loc = conf['UWSGI']
        self.app_bind_port = conf['APPBIND']
        self.home = conf['DARKCHOCO_HOME']
        
        command =[self.uwsgi_loc, '--plugins', 'python', 
                '--socket', self.app_bind_port,
                '--wsgi-file', '%s/lib/darkchoco/application.py' % (self.home),
                '--enable-threads', '--logto',
                '%s/uwsgi.log' % (self.log_loc),
                '--pidfile', '%s/uwsgi.pid' % (self.temp_loc),
                '--buffer-size=32768']
        super().__init__(name = "uWsgi Service", command=command)
    
    def reload_conf(self):
        self.send_signal(signal.SIGHUP)            
    
        if not self._isrunning():
            print("ERROR: Process <%s> is already stopped." \
                  " Ignoring stop request" % self.name)
            return False
        os.kill(self.pid, signal.SIGQUIT)
        if not self._isstoppped():
            print("ERROR: Process <%s> not stopped with " \
                  "SIGINT signal, killing the process" % self.name)        
            self.kill()
        return True
        
class _Location:

    def __init__(self):
        self.path = None
        self.values = []
    
    def add_value(self, key, value):
        self.values.append([key, value])
        
class _NginxConf:
    
    def __init__(self, conf):
        self.listen = conf['WEBBIND']
        self.host_name = conf['DARKCHOCO_HOST_NAME']
        self.root = conf['DARKCHOCO_APPS']
        
        self.locations = []
        self.root_location = None
    
    def add_location(self, location):
        self.locations.append(location)
        
class Nginx(Process):
    
    def __init__(self, conf):
    
        self.nginxconf = _NginxConf(conf)
        
        self.app_loc = conf['DARKCHOCO_APPS']
        self.temp_loc = conf['DARKCHOCO_TMP']
        self.share_loc = conf['DARKCHOCO_SHARE']
        self.log_loc = conf['DARKCHOCO_LOGS']
        self.nginx_loc = conf['NGINX']
        self.app_bind_port = conf['APPBIND']
        self.generate_conf_file()
        
        command =[self.nginx_loc, '-c', '{tmp}/nginx.conf'.format(tmp=self.temp_loc)]
        
        super().__init__(name = "Nginx Service", command = command)
        
    def reload_conf(self):
        self.send_signal(signal.SIGHUP)
        
    def generate_conf_file(self):
        webapps = Webapps.get_app_details_with_minimal_init(self.app_loc)
        
        for webapp in webapps:
            location = _Location()
            if len(webapp.url_prefix) > 0:
                location.path = '/%s/(.+\..+)' % (webapp.url_prefix)
                location.add_value('alias', '%s/%s/static/$1' % (
                                        self.app_loc,
                                        webapp.foldername))
                self.nginxconf.add_location(location)
            else:
                location.path = '/(.+\..+)'
                location.add_value('alias', '%s/%s/static/$1' % (
                                        self.app_loc,
                                        webapp.foldername))
                self.nginxconf.root_location = location
                
        conf = "\npid  %s/nginx.pid;" % (self.temp_loc)
        conf += "\n\nevents {"
        conf += "\n\tworker_connections  1024;"
        conf += "\n}"
        
        conf += "\n\nhttp {"
        conf += "\n\tinclude      %s/mime.types;" % (self.share_loc)
        conf += "\n\tdefault_type  application/octet-stream;"
        conf += "\n\tsendfile        on;"
        conf += "\n\tkeepalive_timeout  65;"
        
        conf += """\n\tlog_format  main  '$remote_addr - $remote_user """
        conf += """[$time_local] "$request" '"""
        conf += """\n\t'$status $body_bytes_sent "$http_referer" '"""
        conf += """\n\t'"$http_user_agent" "$http_x_forwarded_for"';"""
        
        conf += "\n\n\tupstream darkchoco {"
        appbind = self.app_bind_port
        if not re.match(".*\..*\..*\..*:.*", appbind):
            appbind = "unix://" + appbind
        conf += "\n\t\tserver %s;" % (appbind)
        conf += "\n\t}"
        
        conf += "\n\n\tserver {"
        conf += "\n\t\tlisten %s;" % (self.nginxconf.listen)
        conf += "\n\t\tserver_name %s;" %(self.nginxconf.host_name)
        conf += "\n\t\troot %s;" % (self.nginxconf.root)
        conf += "\n\t\taccess_log %s/nginx.access.log  main;" % (
                            self.log_loc)
        
        for loc in self.nginxconf.locations:
            conf += "\n\n\t\tlocation ~ %s {" % (loc.path)
            for val in loc.values:
                conf += "\n\t\t\t%s %s;" % (val[0], val[1])
            conf += "\n\t\t}"
        
        if self.nginxconf.root_location:
            conf += "\n\n\t\tlocation ~ %s {" % (
                                            self.nginxconf.root_location.path)
            for val in self.nginxconf.root_location.values:
                conf += "\n\t\t\t%s %s;" % (val[0], val[1])
            conf += "\n\t\t}"
        
        conf += "\n\n\t\tlocation / {"
        conf += "\n\t\t\tuwsgi_pass darkchoco;"
        conf += "\n\t\t\tinclude %s/uwsgi_params;" % (self.share_loc)
        conf += "\n\t\t}"
        conf += "\n\t}"
        conf += "\n}"
        
        f = open("%s/nginx.conf" % (self.temp_loc), "w")
        f.write(conf)
        f.close()

class AppServer():
    
    def __init__(self, conf):
        self.uwsgi = Uwsgi(conf)
        self.nginx = Nginx(conf)
        
    def start(self):
        self.uwsgi.start()
        self.nginx.start()
        
    def stop(self):
        self.nginx.stop()
        self.uwsgi.stop()    
        
    def reload(self):
        self.uwsgi.reload_conf(conf)
        self.nginx.reload_conf(conf)
    
    def restart(self):
        self.stop()
        self.start()
    
    def join(self):
        first = True
        while True:
            try:
                if not self.isrunning():
                    break
                if first:
                    print("INFO: Services started up")
                    first = False
                        
                time.sleep(2)
            except NotStartedYet:
                print("INFO: Waiting for service to startup") 
                time.sleep(2)
            
    def isrunning(self):
        if self.uwsgi.isrunning() and self.nginx.isrunning():
            return True
        else:
            if self.uwsgi.isrunning():
                print("SEVERE: Nginx service stopped unexpectedly")
                print("SEVERE: So, stopping uWsgi service as well")
                self.uwsgi.stop()
            elif self.nginx.isrunning():
                print("SEVERE: uWsgi service stopped unexpectedly")
                print("SEVERE: So, stopping Nginx service as well")
                self.nginx.stop()

            return False

                
if __name__ == "__main__":
    if not precheck():
        print("Precheck failed. Node not started ....")
        sys.exit(-1)
    else:
        if len(sys.argv) == 2 and sys.argv[1] in ("--daemon", "-d"):
            try:
                f = os.fork()
            except OSError as e:
                print("SEVERE: Error forking.. <{fork}>".format(fork=e))
                print("SEVERE: Trace -> {trace}".format(
                                             trace=traceback.format_exc()))
            if f != 0:
                print("INFO: Darkchoco server is invoked to start as daemon")
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
                
                rw = open("/dev/null", "r+")
                os.dup2(rw.fileno(), 0)
                os.dup2(rw.fileno(), 1)
                os.dup2(rw.fileno(), 2)
                print("INFO: Starting darkchoco in daemon mode ...")
        logger = Logger(Logger.INFO)
        print(os.environ['DARKCHOCO_LOGS'] + "/server.log")
        logger.initialize(
               open(os.environ['DARKCHOCO_LOGS'] + "/server.log", "w"))
        f = open(os.environ['DARKCHOCO_TMP'] + "/darkchoco.pid", "w")
        f.write(str(os.getpid()))
        f.close()
        conf_list = ['DARKCHOCO_HOME',
                    'DARKCHOCO_SHARE',
                    'DARKCHOCO_LIBS',
                    'DARKCHOCO_APPS',
                    'DARKCHOCO_TMP',
                    'DARKCHOCO_CONFIG',
                    'DARKCHOCO_DATA',
                    'DARKCHOCO_LOGS',
                    'DARKCHOCO_HOST_NAME',
                    'APPBIND',
                    'WEBBIND',
                    'BLOCK_SIZE',
                    'SESS_AES_KEY',
                    'PYTHON',
                    'NGINX',
                    'UWSGI',
                    ]
        conf = {}
        for list_item in conf_list:
             conf[list_item] = os.environ[list_item]
        appserver = AppServer(conf)
        
        def handler(signum, frame):
            print('Receive signal : ', signum)
            if signum in (signal.SIGTERM, signal.SIGINT, signal.SIGABRT):
                print("INFO: Stopping darkchoco service")
                appserver.stop()
                print("INFO: Darkchoco services stopped")
            elif signum == signal.SIGHUP:
                print("INFO: Reloading darkchoco conf files")
                appserver.reload()
            else:
                print("INFO: Ignoring signal")
    
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGABRT, handler)
        signal.signal(signal.SIGHUP, handler)
        appserver.start()
        appserver.join()
        print("Services stopped")

