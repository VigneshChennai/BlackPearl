#!/usr/bin/env python

import os

from darkchoco.core import webapps as Webapps

class Location:

    def __init__(self):
        self.path = None
        self.values = []
    
    def add_value(self, key, value):
        self.values.append([key, value])
        
class NgnixConf:
    
    def __init__(self):
        self.listen = os.environ['WEBPORT']
        self.server_name = os.environ['DARKCHOCO_SERVER_NAME']
        self.root = os.environ['DARKCHOCO_APPS']
        
        self.locations = []
        self.root_location = None
    
    def add_location(self, location):
        self.locations.append(location)
        
def generate_nginx_conf(location):
    webapps = Webapps.get_app_details_with_minimal_init(location)
    nginxConf = NgnixConf()
    
    for webapp in webapps:
        location = Location()
        if len(webapp.url_prefix) > 0:
            location.path = '/%s/(.+\..+)' % (webapp.url_prefix)
            location.add_value('alias', '%s/%s/static/$1' % (
                                    os.environ['DARKCHOCO_APPS'],
                                    webapp.foldername))
            nginxConf.add_location(location)
        else:
            location.path = '/(.+\..+)'
            location.add_value('alias', '%s/%s/static/$1' % (
                                    os.environ['DARKCHOCO_APPS'],
                                    webapp.foldername))
            nginxConf.root_location = location
            
    conf = "\npid  %s/nginx.pid;" % (os.environ['DARKCHOCO_TMP'])
    conf += "\n\nevents {"
    conf += "\n\tworker_connections  1024;"
    conf += "\n}"
    
    conf += "\n\nhttp {"
    conf += "\n\tinclude       mime.types;"
    conf += "\n\tdefault_type  application/octet-stream;"
    conf += "\n\tsendfile        on;"
    conf += "\n\tkeepalive_timeout  65;"
    
    conf += """\n\tlog_format  main  '$remote_addr - $remote_user [$time_local] "$request" '"""
    conf += """\n\t'$status $body_bytes_sent "$http_referer" '"""
    conf += """\n\t'"$http_user_agent" "$http_x_forwarded_for"';"""
    
    conf += "\n\n\tupstream darkchoco {"
    conf += "\n\t\tserver 127.0.0.1:%s;" % (os.environ['APPPORT'])
    conf += "\n\t}"
    
    conf += "\n\n\tserver {"
    conf += "\n\t\tlisten %s;" % (nginxConf.listen)
    conf += "\n\t\tserver_name %s;" %(nginxConf.server_name)
    conf += "\n\t\troot %s;" % (nginxConf.root)
    conf += "\n\t\taccess_log %s/nginx.access.log  main;" % (os.environ['DARKCHOCO_LOGS'])
    
    for loc in nginxConf.locations:
        conf += "\n\n\t\tlocation ~ %s {" % (loc.path)
        for val in loc.values:
            conf += "\n\t\t\t%s %s;" % (val[0], val[1])
        conf += "\n\t\t}"
    
    if nginxConf.root_location:
        conf += "\n\n\t\tlocation ~ %s {" % (nginxConf.root_location.path)
        for val in nginxConf.root_location.values:
            conf += "\n\t\t\t%s %s;" % (val[0], val[1])
        conf += "\n\t\t}"
    
    conf += "\n\n\t\tlocation / {"
    conf += "\n\t\t\tuwsgi_pass darkchoco;"
    conf += "\n\t\t\tinclude uwsgi_params;"
    conf += "\n\t\t}"
    conf += "\n\t}"
    conf += "\n}"
    
    return conf
    
if __name__ == '__main__':
    conf = generate_nginx_conf(os.environ['DARKCHOCO_APPS'])
    f = open("%s/ngnix.conf" % (os.environ['DARKCHOCO_TMP']), "w")
    f.write(conf)
    f.close()
