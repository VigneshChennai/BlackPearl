#!/bin/bash

usage () {
    cat << EOF
    
**Usage**

Syntax: darkchoco.sh <option>

Options:
    1. startup
    2. shutdown

EOF

}

if [ "$#" != 1 ]
then
    usage;
    exit -1
fi

CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $CURDIR/config.sh

if [ -e $DARKCHOCO_TMP/nginx.pid ]
then
    NGINX_PID=$(cat $DARKCHOCO_TMP/nginx.pid)
fi

if [ -e $DARKCHOCO_TMP/uwsgi.pid ]
then
    UWSGI_PID=$(cat $DARKCHOCO_TMP/uwsgi.pid)
fi

if [ "$1" == "shutdown" ]
then
    echo
    echo "Stopping Darkchoco services in localhost"\
         " running on <$USER> user account"
    echo
         
    if [ -e "$DARKCHOCO_TMP" ]
    then
        echo -n "Trying to stop nginx service ..."
        if [ $NGINX_PID"x" == "x" ]
        then
            echo " [Failed] nginx service is not currently running"
            
        elif ! kill $NGINX_PID > /dev/null 2>&1;
        then
            echo " [Failed] Unable to stop nginx service. May be it is already stopped."
        else
            echo " [Stopped]"
        fi
        
        echo -n "Trying to stop uWsgi service ..."
        if [ $UWSGI_PID"x" == "x" ]
        then
            echo " [Failed] uWsgi service is not currently running"
            
        elif ! kill $UWSGI_PID > /dev/null 2>&1;
        then
            echo " [Failed] Unable to stop uwsgi service. May be it is already stopped."
            rm $DARKCHOCO_TMP/uwsgi.pid
        else
            echo " [Stopped]"
            rm $DARKCHOCO_TMP/uwsgi.pid
        fi
        
        echo
        echo "Darkchoco service is stopped"
        echo
    else
        echo "Darkchoco service is not running."
        exit 0
    fi
    
    exit 0
    
elif [ "$1" == "startup" ]
then
    if [ -e "$DARKCHOCO_TMP" ]
    then
        if kill -0 $NGINX_PID > /dev/null 2>&1;
        then
            echo "Darkchoco is currently running. "\
                 "Shut it down before starting it up again."
            exit -1
        fi
        
        if kill -0 $UWSGI_PID > /dev/null 2>&1;
        then
            echo "Darkchoco is currently running. "\
                 "Shut it down before starting it up again."
            exit -1
        fi
    fi
else
    echo
    echo "Invalid option : $1"
    usage;
    exit -1
fi
mkdir -p $DARKCHOCO_TMP
mkdir -p $DARKCHOCO_LOGS

rm -f $DARKCHOCO_TMP/* > /dev/null 2>&1;

echo "Starting darkchoco server"

echo -n "Starting uWsgi service ..."
uwsgi --plugins python --socket :$APPPORT \
        --wsgi-file "$DARKCHOCO_HOME/darkchoco/application.py" --enable-threads \
        --daemonize "$DARKCHOCO_LOGS/uwsgi.log" --pidfile $DARKCHOCO_TMP/uwsgi.pid

echo "uWsgi service [Started]"
echo

echo -n "Generating configuration files for nginx ..."
cat > $DARKCHOCO_TMP/uwsgi_params <<EOF

uwsgi_param  QUERY_STRING       \$query_string;
uwsgi_param  REQUEST_METHOD     \$request_method;
uwsgi_param  CONTENT_TYPE       \$content_type;
uwsgi_param  CONTENT_LENGTH     \$content_length;

uwsgi_param  REQUEST_URI        \$request_uri;
uwsgi_param  PATH_INFO          \$document_uri;
uwsgi_param  DOCUMENT_ROOT      \$document_root;
uwsgi_param  SERVER_PROTOCOL    \$server_protocol;
uwsgi_param  HTTPS              \$https if_not_empty;

uwsgi_param  REMOTE_ADDR        \$remote_addr;
uwsgi_param  REMOTE_PORT        \$remote_port;
uwsgi_param  SERVER_PORT        \$server_port;
uwsgi_param  SERVER_NAME        \$server_name;

EOF

cat > $DARKCHOCO_TMP/mime.types <<EOF

types {
    text/html                             html htm shtml;
    text/css                              css;
    text/xml                              xml;
    image/gif                             gif;
    image/jpeg                            jpeg jpg;
    application/javascript                js;
    application/atom+xml                  atom;
    application/rss+xml                   rss;

    text/mathml                           mml;
    text/plain                            txt;
    text/vnd.sun.j2me.app-descriptor      jad;
    text/vnd.wap.wml                      wml;
    text/x-component                      htc;

    image/png                             png;
    image/tiff                            tif tiff;
    image/vnd.wap.wbmp                    wbmp;
    image/x-icon                          ico;
    image/x-jng                           jng;
    image/x-ms-bmp                        bmp;
    image/svg+xml                         svg svgz;
    image/webp                            webp;

    application/font-woff                 woff;
    application/java-archive              jar war ear;
    application/json                      json;
    application/mac-binhex40              hqx;
    application/msword                    doc;
    application/pdf                       pdf;
    application/postscript                ps eps ai;
    application/rtf                       rtf;
    application/vnd.apple.mpegurl         m3u8;
    application/vnd.ms-excel              xls;
    application/vnd.ms-fontobject         eot;
    application/vnd.ms-powerpoint         ppt;
    application/vnd.wap.wmlc              wmlc;
    application/vnd.google-earth.kml+xml  kml;
    application/vnd.google-earth.kmz      kmz;
    application/x-7z-compressed           7z;
    application/x-cocoa                   cco;
    application/x-java-archive-diff       jardiff;
    application/x-java-jnlp-file          jnlp;
    application/x-makeself                run;
    application/x-perl                    pl pm;
    application/x-pilot                   prc pdb;
    application/x-rar-compressed          rar;
    application/x-redhat-package-manager  rpm;
    application/x-sea                     sea;
    application/x-shockwave-flash         swf;
    application/x-stuffit                 sit;
    application/x-tcl                     tcl tk;
    application/x-x509-ca-cert            der pem crt;
    application/x-xpinstall               xpi;
    application/xhtml+xml                 xhtml;
    application/xspf+xml                  xspf;
    application/zip                       zip;

    application/octet-stream              bin exe dll;
    application/octet-stream              deb;
    application/octet-stream              dmg;
    application/octet-stream              iso img;
    application/octet-stream              msi msp msm;

    application/vnd.openxmlformats-officedocument.wordprocessingml.document    docx;
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet          xlsx;
    application/vnd.openxmlformats-officedocument.presentationml.presentation  pptx;

    audio/midi                            mid midi kar;
    audio/mpeg                            mp3;
    audio/ogg                             ogg;
    audio/x-m4a                           m4a;
    audio/x-realaudio                     ra;

    video/3gpp                            3gpp 3gp;
    video/mp2t                            ts;
    video/mp4                             mp4;
    video/mpeg                            mpeg mpg;
    video/quicktime                       mov;
    video/webm                            webm;
    video/x-flv                           flv;
    video/x-m4v                           m4v;
    video/x-mng                           mng;
    video/x-ms-asf                        asx asf;
    video/x-ms-wmv                        wmv;
    video/x-msvideo                       avi;
}

EOF

cd "$CURDIR"
python nginx.py > /dev/null 2>&1

echo " [Completed]"
echo -n "Starting nginx serive ..."
nginx -c "$DARKCHOCO_TMP/ngnix.conf" > /dev/null  2>&1 < /dev/null&
disown $!
echo " [Started]"
echo
echo "Log files are generated at <$DARKCHOCO_LOGS>"
echo
