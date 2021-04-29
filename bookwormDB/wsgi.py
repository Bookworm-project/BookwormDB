from bookwormDB.general_API import DuckDBCall, Caching_API, ProxyAPI
import json
from urllib.parse import unquote
import logging
import multiprocessing
import gunicorn.app.base
from bookwormDB.store import store
from .store import store
from .query_cache import Query_Cache
from pathlib import Path
import duckdb

from datetime import datetime


def content_type(query):
    try:
        format = query['format']
    except:
        return 'text/plain'

    if format == "json":
        return "application/json"

    if format == "json_c":
        return "application/json"

    if format == "feather":
        return "application/octet-stream"

    if format == "html":
        return "text/html"

    return 'text/plain'


args = store()['args']
if args.cache != "none":
    query_cache = Query_Cache(
        args.cache,
        max_entries = 256,
        max_length = 2**8,
        cold_storage = args.cold_storage)


class DuckPool(dict):
    def __missing__(self, key):
        # Mother duck said 'quack quack quack quack'
        # and all of her five little duckies came back.
        duck_dir = store()['duckdb_directory']
        self[key] = duckdb.connect(str(Path(duck_dir) / key), read_only = True)
        return self[key]

duck_connections = DuckPool()

if args.remote_host is None:
    logging.info("Using SQL API")
    API = DuckDBCall
    API_kwargs = {
    }

else:
    logging.info("Using proxy API")
    API = ProxyAPI
    API_kwargs = {
        "endpoint": args.remote_host
    }



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
    except:
        ip = environ.get('REMOTE_ADDR')
    if ip is None:
        ip = environ.get('REMOTE_ADDR')

    # Caching IPs directly is probably in violation of GPDR.
    # It's nice to have session browsing data, so we'll grab just the
    # last byte which should be enough to get something out of.
    ip = ip.split(".")[-1]

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

    args = store()['args']

    if args.cache == "none":
        process = API(query=query, db=duck_connections[query['database']], **API_kwargs) 
    else:
        process = Caching_API(query, query_cache, API, **API_kwargs)

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
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def run(port = 10012, bind="0.0.0.0", workers = number_of_workers()):
    """
    port: the service port
    bind: the host to bind to. Requests that don't match this address
          will be ignored. The default accepts all connections: 127.0.0.1 listens
          only to localhost.
    """
    if workers==0:
        workers = number_of_workers()

    options = {
        'bind': f'{bind}:{port}',
        'workers': workers,
    }

    StandaloneApplication(application, options).run()
