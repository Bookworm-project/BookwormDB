from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
import ujson as json
from urllib.parse import unquote
import logging
import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems
from datetime import datetime

def content_type(query):
    try:
        format = query['format']
    except:
        return 'text/plain'
    
    if format == "json":
        return "application/json"
    
    if format == "feather":
        return "application/octet-stream"
    
    if format == "html":
        return "text/html"
    
    return 'text/plain'

def application(environ, start_response, logfile = "bookworm_queries.log"):
    # Starting with code from http://wsgi.tutorial.codepoint.net/parsing-the-request-post
    try:
        request_body_size = int(environ.get('QUERY_STRING', 0))
    except (ValueError):
        request_body_size = 0

    # When the method is POST the variable will be sent
    # in the HTTP request body which is passed by the WSGI server
    # in the file like wsgi.input environment variable.

    q = environ.get('QUERY_STRING')
    try:
        ip = environ.get('HTTP_X_FORWARDED_FOR')
 #       logging.debug("Request from {}".format(ip))
    except:
        ip = environ.get('REMOTE_ADDR')
    if ip is None:
        ip = environ.get('REMOTE_ADDR')
    query = unquote(q)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
        'Access-Control-Allow-Headers':
        'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token',
        'charset': 'utf-8'
    }


        
    logging.debug("Received query {}".format(query))
    start = datetime.now()

    # Backward-compatability: we used to force query to be
    # a named argument.
    query = query.strip("query=")
    query = query.strip("queryTerms=")
                          
    try:
        query = json.loads(query)
        query['ip'] = ip
    except:
        response_body = "Unable to read JSON"
        status = '404'
        start_response(status, list(headers.items()))
        return [b'{"status":"error", "message": "You have passed invalid JSON to the Bookworm API"}']

    process = SQLAPIcall(query)
    response_body = process.execute()

    # It might be binary already.
    headers['Content-type'] = content_type(query)
    
    if headers['Content-type'] != 'application/octet-stream':
        response_body = bytes(response_body, 'utf-8')
                    
    headers['Content-Length'] = str(len(response_body))
    status = '200 OK'
    start_response(status, list(headers.items()))

    query['time'] = start.timestamp()
    query['duration'] = datetime.now().timestamp() - start.timestamp()
    # This writing isn't thread-safe; but generally we're not getting more than a couple queries a second.
    with open(logfile, 'a') as fout:
        json.dump(query, fout)
        fout.write("\n")
    logging.debug("Writing to log: \n{}\n".format(json.dumps(query)))
    return [response_body]

# Copied from the gunicorn docs.


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """
    Superclassed to allow bookworm to do the running.
    """
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
    
