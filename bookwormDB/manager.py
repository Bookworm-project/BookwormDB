import re

from pathlib import Path
import sys
import os
import bookwormDB
import argparse
import json
import nonconsumptive as nc
from .store import store
import logging
from nonconsumptive.commander import namespace_to_kwargs, add_builder_parameters
logger = logging.getLogger("bookworm")

"""
This is the code that actually gets run from the command-line executable.

The BookwormManager class defines some methods for controlling bookworm SQL instances
and running upkeep operations;
the run_arguments function pulls commands from the command line. Any useful new bookworm methods
should be passed through run_arguments to work.

"""

class BookwormManager(object):
    """
    This class is passed some options that tell it the name of the bookworm it's working on;
    some of the methods here are the directly callable as the command line arguments.
section'client'
    This is what calls the various other bookworm scripts, whether Python or not.
    """

    def __init__(self, cnf_file=None, database=None):

        # This will likely be changed if it isn't None.
        import configparser

        self.basedir = None
        self.dbname = None

        # More specific options override the config file
        if database is not None:
            # Passed in dbname takes precedence over config file.
            self.dbname = database

    def config(self,args):
        """
        Performs useful configuration tasks, such as setting up a MySQL installation.
        """
        if args.target=="apache":
            from bookwormDB.configuration import apache
            apache()

    def query(self, args):
        """
        Run a query against the API from the command line.
        """

        from bookwormDB.general_API import DuckDBCall
        import json
        import duckdb
        query = args.APIcall
        logger.info(query)
        con = duckdb.connect("/drobo/bookworm_dbs/" + query['database'], read_only = True)
        caller = DuckDBCall(query = query, con = con)
        logger.info(caller.execute())

    def serve(self, args):

        """
        Serve the api.
        """

        from bookwormDB.wsgi import run
        run(args.port, args.bind, args.workers)

    def build(self, args):
        from .builder import BookwormCorpus
        nc_params = namespace_to_kwargs(args)
        db_path = args.db_directory / args.database
        corp = BookwormCorpus(
            db_location = db_path,
            **nc_params,
            cache_set = {"tokenization", "word_counts",
                            "encoded_unigrams", "document_lengths"})
        corp.build()
        

    def add_metadata(self, args):
        raise NotImplementedError("Functionality missing in 3.0")

def run_arguments():
    """
    Parse the command line arguments and run them.

    The actual running is handled by an instance of the class `BookwormManager`,
    which calls all bookworm-related arguments; that, in turn, calls some specific
    methods to make things happen (the most important of which is the `BookwormDB`
    class, which is in charge of MySQL calls).

    I apologize for how ugly and linear this code is: it's not clear to me
    how to write pretty modular code with the argparse module.
    You just end up with a bunch of individual add argument lines that are full of random text.
    Refactoring pull requests welcome.
    """

    parser = argparse.ArgumentParser(
        description='Build and maintain a Bookworm database.',
        prog="bookworm")
    parser.add_argument("--configuration","-c",help="The name of the configuration file to read options from: by default, 'bookworm.cnf' in the current directory.", default="bookworm.cnf")


    parser.add_argument("--log-level", "-l",
        help="The logging detail to use for errors."
            "Default is 'warning', only significant problems; info gives a "
            "fuller record, and 'debug' dumps many db queries, etc.",
            choices=["warning","info","debug"],type=str.lower,default="warning")

    parser.add_argument("--ngrams",nargs="+",default=["unigrams"],help="What levels to parse with. Multiple arguments should be unquoted in spaces. This option currently does nothing.")

    parser.add_argument("--db-directory", required = True, help = ""
        "Directory where duckdb databases live.", type = Path)

    parser.add_argument("--database", "-d", help = ""
        "The database name inside db-folder for this command. "
        "Not relevant for 'serve' commands.",
        default = None
    )
 
    # Use subparsers to have an action syntax, like git.
    subparsers = parser.add_subparsers(title="action",
      help='The commands to run with Bookworm',
      dest="action")

    ############# build #################

    build_parser = subparsers.add_parser("build",
      description = "Create files",
      help="Build up the component parts of a Bookworm. " 
        "if you specify something far along the line")

    # Inherited directly from nonconsumptive.commander.
    add_builder_parameters(build_parser)

    ############# supplement #################
    supplement_parser = subparsers.add_parser("add_metadata",help="""Supplement the\
    metadata for an already-created Bookworm with new items. They can be keyed to any field already in the database.""")
    supplement_parser.add_argument("-f","--file",help="""The location of a file with additional metadata to incorporate into your bookworm.""",required=True)


    # Serve the current bookworm

    serve_parser = subparsers.add_parser("serve",
                                         help="Serve the bookworm. Be default this is an API endpoint,"
                                         "served over gunicorn, or (not yet supported) a full installation. You might want to wrap"
"the gunicorn endpoint behind a more powerful webserver like apache or nginx.")

    serve_parser.add_argument("--full-site", action = "store_true", help="Serve a webpage as well as a query endpoint? Not active.")
    serve_parser.add_argument("--port", "-p", default="10012", help="The port over which to serve the bookworm", type=int)
    serve_parser.add_argument("--bind", "-b", default="127.0.0.1", help="The IP address to bind the server to.", type=str)
    serve_parser.add_argument("--workers", "-w", default="0", help="How many gunicorn worker threads to launch for the API. Reduce if you're seeing memory issues.",type=int)
    serve_parser.add_argument("--dir","-d",default="http_server",help="A filepath for a directory to serve from. Will be created if it does not exist.")
#    serve_parser.add_argument("--API", "-a", default="MySQL",
#                                help="The type of API endpoint to run. 'MySQL' will"
#                                      "will run MySQL")
    serve_parser.add_argument("--cache", default = "none",
                                help="cache locations?")
    serve_parser.add_argument("--cold-storage", default = "none",
                                help="A folder with cached query results. Allows long-term cold-storage.")                                                            
    serve_parser.add_argument("--remote-host", default = None,
                                help="Hosts to pass queries through to. If enabled.")


    # Configure the global server.
    configure_parser = subparsers.add_parser("config",help="Some helpers to configure a running bookworm, or to manage your server-wide configuration.")
    configure_parser.add_argument("target",help="The thing you want help configuring.",choices=["mysql", "mysql-info", "apache"])
    configure_parser.add_argument("--users",nargs="+",choices=["admin","global","root"],help="The user levels you want to act on.",default=["admin","global"])
    configure_parser.add_argument("--force","-f",help="Overwrite existing configurations in potentially bad ways.",action="store_true",default=False)


    configure_parser = subparsers.add_parser("query", help="query the API directly. Inefficient compared to using a running host.")
    configure_parser.add_argument("APIcall", help="A JSON string.", type = json.loads)


    # Call the function
    args = parser.parse_args()
    # stash those away.
    store()['args'] = args
    # Set the logging level based on the input.
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    # While we're at it, log with line numbers
    FORMAT = "[%(filename)s:%(lineno)s-%(funcName)s() %(asctime)s.%(msecs)03d] %(message)s"
    logging.basicConfig(format=FORMAT, datefmt="%I:%M:%S")
    for logger_name in ["nonconsumptive", "bookworm"]:
        logging.getLogger(logger_name).setLevel(numeric_level)

    logger.info("Info logging enabled.")
    logger.debug("Debug logging enabled.")

    # Create the bookworm
    my_bookworm = BookwormManager(args.configuration, args.database)

    # Call the current action with the arguments passed in.
    # bookworm build --carefully
    # becomes
    # BookwormMangager.build(carefully = True)
    getattr(my_bookworm, args.action)(args)
