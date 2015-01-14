#!/bin/env python

################################################################################
#                  BlackPearl Application configuration file 
#                                   
# Application Name : Sample testing applciations
# Author :  Vigneshwaran P 
# Website : www.vigneshchennai.in 
# Email Address : vigneshchennai@live.in
#
################################################################################


name= "Sample testing applciations"

#URL Prefix for the webapplication.
#
#If it is not specifed, the foldername of the webapplication will be taken as
#url_prefix
#
#A url_prefix "ROOT" will make the application to hosted on the root level.
#
#Example :-
# if url_prefix="dwm"
# then the application will be deployed at "www.example.com/dwm"
#
# if url_prefix="ROOT"
# then the application will be deployed at "www.example.com"
#

url_prefix="newapp"

#Handlers are the list of python files which holds the python web modules.
#
#The functions which are using @weblocation decorate but not in the below listed
#python files will be ignored.
#
#Example : if python file is (Webapp/hander.py)
#then
#handlers = ['Webapp.hander']

handlers = ["newapp.handlers"]

#If sessions are not used in the application, the below should be set to False
session_enabled = True


#List of python function which need to process the incoming request before
#handing it to the webmodules
#
#This is not the python files, it should the list of fulle python function name
#
#Example : if python function "preprocessor" listed under Webapp/hander.py file
#then
#posthanlder = ['Webapp.hander.preprocessor'}

preprocessors = []

#List of python function which need to process the outgoing request after
#the webmodules processed the request.
#
#This is not the python files, it should the list of full python function name
#
#Example : if python function "posthandler" listed under Webapp/hander.py file
#then
#posthanlder = ['Webapp.hander.posthandler'}

posthandlers = []

