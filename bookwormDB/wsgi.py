#!/usr/bin/env python

from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
import ujson as json
from urllib.parse import unquote
import logging

def content_type(query):
    method = query['format']
    if method == "json":
        return "application/json"
    if method == "feather":
        return "application/octet-stream"
    return 'text/plain'

def application(environ, start_response):
    # Starting with code from http://wsgi.tutorial.codepoint.net/parsing-the-request-post
    try:
        request_body_size = int(environ.get('QUERY_STRING', 0))
    except (ValueError):
        request_body_size = 0

    # When the method is POST the variable will be sent
    # in the HTTP request body which is passed by the WSGI server
    # in the file like wsgi.input environment variable.

    q = environ.get('QUERY_STRING')
    query = unquote(q)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
        'Access-Control-Allow-Headers':
        'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token',
        'charset': 'utf-8'
    }


    # Backward-compatability.

    logging.debug("Received query {}".format(query))
    query = query.strip("query=")
                          
    try:
        query = json.loads(query)
    except:
        response_body = "Unable to read JSON"
        status = '404'
        start_response(status, list(headers.items()))
        return [b"This is a Bookworm JSON query endpoint. You must pass valid JSON."]

    process = SQLAPIcall(query)
    response_body = process.execute()

    # It might be binary already.
    headers['Content-type'] = content_type(query)
    
    if headers['Content-type'] != 'application/octet-stream':
        response_body = bytes(response_body, 'utf-8')
                    
    headers['Content-Length'] = str(len(response_body))
    status = '200 OK'
    start_response(status, list(headers.items()))
    return [response_body]

# Copied from the gunicorn docs.

import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems

def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def run(port = 10012, workers = number_of_workers()):
    if workers==0:
        workers = number_of_workers()
        
    options = {
        'bind': '{}:{}'.format('127.0.0.1', port),
        'workers': workers,
    }
    
    StandaloneApplication(application, options).run()
    
