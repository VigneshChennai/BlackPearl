#Readme for creating webapps



##Structure of webapp

	webapps
	    :
	    :
	    :-->App1 (Folder name of the webapp)
	    :     :
	    :     :--> config.py
	    :     :
	    :     :--> static
	    :     :
	    :     :--> test
	    :
	    :-->App2 (Folder name of the webapp)
	    :     :
	    :     :--> config.py
	    :     :
	    :     :--> static
	    :     :
	    :     :--> test
	    :
	    :--> .....


##config.py - Available options


####1. name

Name of the application which gets displayed in darkchoco
Admin Console

#####Note
    It is Optional, if not specified, folder name is
    taken as "Application name"

#####Example

    name="Application Name"

####2. url_prefix

Used to specify prefix to the application url

#####Note
    It is Optional, if not specified, folder name is
    taken as "url_prefix"

#####Example

    url_prefix = "ROOT" #for the app to handle
                        #the root level url request

    url_prefix = "app1" #for the app to handle all the request having
                        #the url /app1/*

####3. handlers


List of python module which contains the request handlers should
be listed below.

handlers = [
            "App1.handler1",
            "App1.handler2"
            ]


