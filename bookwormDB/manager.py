from __future__ import print_function
import re
import logging
import sys
import os
import bookwormDB
import argparse
import nonconsumptive as nc
from .store import store

"""
This is the code that actually gets run from the command-line executable.

The BookwormManager class defines some methods for controlling bookworm SQL instances
and running upkeep operations;
the run_arguments function pulls commands from the command line. Any useful new bookworm methods
should be passed through run_arguments to work.


Some modules, especially bookworm-specific ones,
are imported inline in the code here--that substantially
(as in, 1 second to 0.2 seconds) reduces startup time
for the command-line executable,
even though it's not best practice otherwise.
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
        for i in range(10):
            basedir = "../"*i
            if os.path.exists(basedir + ".bookworm"):
                self.basedir = basedir
                break
            if self.basedir==None:
                logging.debug("No bookworm directory found; hopefully this isn't a build call.")

        if cnf_file is not None:
            config = configparser.ConfigParser(allow_no_value=True)
            config.read([cnf_file])
            if config.has_section("client"):
                """
                Silently go along if the config doesn't exist.
                """
                try:
                    self.dbname = config.get("client", "database")
                except configParser.NoOptionError:
                    pass

        # More specific options override the config file
        if database is not None:
            # Passed in dbname takes precedence over config file.
            self.dbname = database

    def config(self,args):
        """
        Performs useful configuration tasks, such as setting up a MySQL installation.
        """
        if args.target=="mysql":
            import bookwormDB.configuration
            bookwormDB.configuration.recommend_my_cnf()
        if args.target=="mysql-info":
            from bookwormDB.configuration import Configfile
            config = Configfile("admin")
            print("The admin configuration login currently being used should be the following.\n")
            config.write_out()
        if args.target=="apache":
            from bookwormDB.configuration import apache
            apache()

    def init(self, args):
        """
        Initialize the current directory as a bookworm directory.
        """
        # Create a configuration file
        if not args.force:
            if os.path.exists(".bookworm"):
                logging.error("""
                You already have a folder named '.bookworm'.
                Probably you've already initialized a Bookworm here.
                """)
                return
            if not os.path.exists("bookworm.cnf"):
                fout = open("bookworm.cnf", "w")
                if self.dbname:
                    loc = self.dbname
                else:
                    loc = os.path.relpath(".", "..")
                    print("Configuring Bookworm named '{}'".format(loc))
                    print("Change the file at bookworm.cnf if this is undesirable".format(loc))
                fout.write("[client]\ndatabase = {}\n".format(loc))
        else:
            fout = open("bookworm.cnf", "w")
            loc = os.path.relpath(".", "..")
            print("Configuring Bookworm named '{}'".format(loc))
            print("Change the file at bookworm.cnf if this is undesirable".format(loc))
            fout.write("[client]\ndatabase = {}\n".format(loc))

    def query(self, args):
        """
        Run a query against the API from the command line.
        """

        from bookwormDB.general_API import DuckDBCall
        import json
        import duckdb
        query = json.loads(args.APIcall)
        logging.info(query)
        con = duckdb.connect("/drobo/bookworm_dbs/" + query['database'], read_only = True)
        caller = DuckDBCall(con, query = query)
        logging.info(caller.execute())

    def serve(self, args):

        """
        Serve the api.
        """

        from bookwormDB.wsgi import run
        run(args.port, args.bind, args.workers)

        import http.server
        from http.server import HTTPServer
        import shutil

        base_dir = args.dir
        base_cgi_dir = os.path.normpath(base_dir + "/" + "cgi-bin")
        d3_dir = os.path.normpath(base_dir + "/" + "D3")
        for dir in [base_dir,base_cgi_dir]:
            if not os.path.exists(dir):
                os.makedirs(dir)

        API = os.path.normpath(os.path.dirname(bookwormDB.__file__) + "/bin/dbbindings.py")
        if not os.path.exists(base_cgi_dir + "/" + API):
            shutil.copy(API, base_cgi_dir)

        if not os.path.exists(d3_dir):
            call(["git","clone","http://github.com/bmschmidt/BookwormD3",d3_dir])

        # Use the Makefile to build the linechartGUI. This is a little Rube Goldberg-y.
        args.target="linechartGUI"

        raise TypeError("The line below this is nonsense")
        self.prep(args)

        os.chdir(base_dir)
        # Actually serve it.
        PORT = args.port

        httpd = HTTPServer(("", PORT), http.server.CGIHTTPRequestHandler)

        print("\n\n" + "****"*20)
        print("A local bookworm server is now running")
        print("You can now view some charts in a web-browser at http://localhost:%d/D3" % PORT)
        print("If you have a time variable, linecharts are at http://localhost:%d/%s" % (PORT,self.dbname))
        print("Please note that this is not a very secure way: if you plan to put your bookworm")
        print("on the open web, consider using apache.")
        httpd.serve_forever()


    def extension(self,args):
        """
        Creates (or updates) an extension
        """

        if not os.path.exists(self.basedir + ".bookworm/extensions"):
            os.makedirs(self.basedir + ".bookworm/extensions")

        my_extension = Extension(args,basedir = self.basedir)
        my_extension.clone_or_pull()
        my_extension.make()

    def build(self, args):
        self.prep(args)

    def prep(self, args):
        """
        This is a wrapper to all the functions define here: the purpose
        is to continue to allow access to internal methods in, for instance,
        the Makefile, without documenting all of them in separate functions.

        That's a little groaty, I know.
        """
        logging.debug(args)

        getattr(self, args.goal)(args)

    def wordlist(self, args):
        """
        Create a wordlist of the top 1.5 million words.
        """
        from .countManager import create_wordlist
        if os.path.exists(".bookworm/texts/wordlist/wordlist.txt"):
            return
        try:
            os.makedirs(".bookworm/texts/wordlist")
        except FileExistsError:
            pass

        input = args.input
        if args.feature_counts:
            logging.info(args.feature_counts)
            input = [a for a in args.feature_counts if 'unigrams' in a][0]
        create_wordlist(n = 1.5e06,
                        input = input,
                        output = ".bookworm/texts/wordlist/wordlist.txt")

    def destroy(self, args):
        self.pristine(args)

    def pristine(self, args):
        # Old name still works.
        import bookwormDB.CreateDatabase
        bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname, variableFile=None)
        if self.dbname == "mysql":
            raise NameError("Don't try to delete the mysql database")
        bookworm.db.query("DROP DATABASE IF EXISTS {}".format(self.dbname))
        import shutil
        try:
            shutil.rmtree('.bookworm')
        except FileNotFoundError:
            pass


    def encoded(self, args):
        """
        Using the wordlist and catalog, create encoded files.
        """
        self.wordlist(args)
        self.derived_catalog(args)

        for k in ['unigrams', 'bigrams', 'trigrams', 'quadgrams', 'completed']:
            try:
                os.makedirs(".bookworm/texts/encoded/{}".format(k))
            except FileExistsError:
                pass
        from .countManager import encode_words

        if args.feature_counts:
            for feature in args.feature_counts:
                encode_words(".bookworm/texts/wordlist/wordlist.txt", feature)
        else:
            encode_words(".bookworm/texts/wordlist/wordlist.txt", args.input)

    def all(self, args):
        self.preDatabaseMetadata(args)
        self.encoded(args)
        self.database_wordcounts(args)
        self.database_metadata(args)

    def preDatabaseMetadata(self, args=None, **kwargs):
        import os
        if not os.path.exists("field_descriptions.json"):
            if os.path.exists("field_descriptions.csv"):
                self.field_descriptions_from_csv()
            else:
                self.guess_field_descriptions()
        self.derived_catalog(args)
        import bookwormDB.CreateDatabase
        # Doesn't need a created database yet, just needs access
        # to some pieces.
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase()
        logging.info("Writing metadata to new catalog file...")
        Bookworm.variableSet.writeMetadata()

        # This creates helper files in the /metadata/ folder.

    def derived_catalog(self, args):

        if not os.path.exists(".bookworm/metadata"):
            os.makedirs(".bookworm/metadata")
        if os.path.exists(".bookworm/metadata/jsoncatalog_derived.txt"):
            return

        from bookwormDB.MetaParser import parse_catalog_multicore, ParseFieldDescs

        logging.debug("Preparing to write field descriptions")
        ParseFieldDescs(write = True)
        logging.debug("Preparing to write catalog")
        parse_catalog_multicore()

    def field_descriptions_from_csv(self):
        import pandas as pd
        import json
        jsonified = pd.read_csv("field_descriptions.csv").to_json(orient="records")
        with open("field_descriptions.json", "w") as fout:
            fout.write(jsonified)

    def guess_field_descriptions(self, args = None, **kwargs):

        """
        Use a number of rules of thumb to automatically generate a field_descriptions.json file.
        This may bin some categories incorrectly (depending on names, for example it may treat dates
        as either categorical or time variables).
        """

        import bookwormDB.CreateDatabase
        import json
        import os
        import pandas as pd
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname, variableFile=None)
        Bookworm.setVariables("jsoncatalog.txt", jsonDefinition=None)
        guess = Bookworm.variableSet.guessAtFieldDescriptions()
        guess = pd.DataFrame(guess)
        guess.to_csv("field_descriptions.csv", index = False)
        raise FileNotFoundError("No field descriptions file found."
         "Creating guess for field descriptions at: field_descriptions.csv."
         "You should probably inspect and edit this file before you build."
         "But if you suspect it's right, you can rebuild again immediately.")

    def reload_memory(self,args):
        import bookwormDB.CreateDatabase
        dbnames = [self.dbname]
        if args.all==True:
            dbnames = []
            datahandler = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,variableFile=None)
            cursor = datahandler.db.query("SELECT TABLE_SCHEMA FROM information_schema.tables WHERE TABLE_NAME='masterTableTable'")
            for row in cursor.fetchall():
                dbnames.append(row[0])
            logging.info("The following databases are bookworms to be reloaded:")
            for name in dbnames:
                logging.info("\t" + name)

        for database in dbnames:
            logging.info("Reloading memory tables for %s" %database)
            Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(database,variableFile=None)
            Bookworm.reloadMemoryTables(force=args.force)

    def database_metadata(self, args):
        import bookwormDB.CreateDatabase
        logging.debug("creating metadata db")
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname)
        Bookworm.variableSet.loadMetadata()

        logging.debug("creating metadata variable tables")

        # This creates a table in the database that makes the results of
        # field_descriptions accessible through the API, and updates the

        Bookworm.loadVariableDescriptionsIntoDatabase()

        Bookworm.create_fastcat_and_wordsheap_disk_tables()

        Bookworm.grantPrivileges()

    def add_metadata(self, args):
        import bookwormDB.CreateDatabase
        import bookwormDB.convertTSVtoJSONarray
        bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,None)
        anchorField = args.key
        if args.format == "tsv":
            # TSV is just converted into JSON in a file at tmp.txt, and slurped in that way.
            if args.key is None:
                args.key = open(args.file).readline().split("\t")[0]
            f = "tmp.txt"
            bookwormDB.convertTSVtoJSONarray.convertToJSON(args.file, f)
            args.file = f

        bookworm.importNewFile(args.file,
                               anchorField=args.key,
                               jsonDefinition=args.field_descriptions)


    def database_wordcounts(self, args = None, **kwargs):
        """
        Builds the wordcount components of the database. This will die
        if you can't connect to the database server.
        """
        cmd_args = args
        import bookwormDB.CreateDatabase

        index = True
        reverse_index = True
        ingest = True
        newtable = True

        if cmd_args and hasattr(cmd_args, "index_only"):
            if cmd_args.index_only:
                ingest = False
                newtable = False
            else:
                index = not cmd_args.no_index
                newtable = not cmd_args.no_delete
            reverse_index = not cmd_args.no_reverse_index
            if not (newtable and ingest and index):
                logging.warn("database_wordcounts args not supported for bigrams yet.")

        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname)
        Bookworm.load_word_list()
        Bookworm.create_unigram_book_counts(newtable=newtable, ingest=ingest, index=index, reverse_index=reverse_index)
        Bookworm.create_bigram_book_counts()

class Extension(object):

    """
    A bookworm extension. Initialized with an args object,
    which has the element url, the location of a clonable git repo.

    Because I don't want people to have to write extensions in python,
    they are build using `make`.
    """

    def __init__(self,args,basedir="./"):
        self.args = args
        self.dir = basedir + ".bookworm/extensions/" + re.sub(".*/","",self.args.url)

    def clone_or_pull(self):
        if not os.path.exists(self.dir):
            logging.info("cloning git repo from " + self.args.url)
            call(["git","clone",self.args.url,self.dir])
        else:
            logging.info("updating pre-existing git repo at " + self.dir)
            Popen(["git","pull"],cwd=self.dir)

    def make(self):
        logging.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        logging.debug("Running make in " + self.dir)
        Popen(["make"], cwd=self.dir)

# Initiate MySQL connection.


# Pull a method from command line input.

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

    parser = argparse.ArgumentParser(description='Build and maintain a Bookworm database.',prog="bookworm")
    parser.add_argument("--configuration","-c",help="The name of the configuration file to read options from: by default, 'bookworm.cnf' in the current directory.", default="bookworm.cnf")

    parser.add_argument("--database","-d",help="The name of the bookworm database in MySQL to connect to: by default, read from the active configuration file.", default=None)

    parser.add_argument("--log-level","-l", help="The logging detail to use for errors. Default is 'warning', only significant problems; info gives a fuller record, and 'debug' dumps many MySQL queries, etc.",choices=["warning","info","debug"],type=str.lower,default="warning")

    parser.add_argument("--input", "-i",
        help = "The location of texts for an initial build."
        "Either a text file ('input.txt' or 'input.txt.gz')"
        "or a folder containing txt or txt.gz files, which may be nested"
        "inside other directories", default = "input.txt")


    parser.add_argument("--feature-counts", action='append',
                                 help="Use pre-calculated feature counts rather than tokenizing complete text on the fly. Supply any number of single files per count level like 'input.unigrams', 'input.bigrams', etc.")

    parser.add_argument("--ngrams",nargs="+",default=["unigrams","bigrams"],help="What levels to parse with. Multiple arguments should be unquoted in spaces. This option currently does nothing.")


    # Use subparsers to have an action syntax, like git.
    subparsers = parser.add_subparsers(title="action", help='The commands to run with Bookworm', dest="action")

    ############# build #################
    build_parser = subparsers.add_parser("build",description = "Create files",help="""Build up the component parts of a Bookworm.\

    if you specify something far along the line (for instance, the linechart GUI), it will\
    build all prior files as well.""")

    build_parser.add_argument("target", help="The make that you want to build. To build a full bookworm, type 'build all'.")

    # Grep out all possible targets from the Makefile

    ############# supplement #################
    supplement_parser = subparsers.add_parser("add_metadata",help="""Supplement the\
    metadata for an already-created Bookworm with new items. They can be keyed to any field already in the database.""")
    supplement_parser.add_argument("-f","--file",help="""The location of a file with additional metadata to incorporate into your bookworm.""",required=True)

    supplement_parser.add_argument(
        "--format",
        help="""The file format of the new metadata.\
        Must be "json" or "tsv". For JSON, the format is the same as the default\
        jsoncatalog.txt (a text file of json lines, each corresponding to a metadata field);\
        for TSV, a tsv with first line of which is column names,\
        and the first column of which is shared key (like filename). The TSV format,\
        particularly without field descriptions, is much easier to use, but doesn't\
        permit multiple values for the same key.""",
        default="json",type=str.lower,choices=["tsv","json"])

    supplement_parser.add_argument("--key",help="""The name of the key. If not specified and input type is TSV, the first column is used.""",default=None)
    supplement_parser.add_argument("--field_descriptions","-d",help="""A description of the new metadata in the format of "field_descriptions.json"; if empty, we'll just guess at some suitable values.""",default=None)

    ######### Reload Memory #############
    memory_tables_parser = subparsers.add_parser("reload_memory",help="Reload the memory\
    tables for the designated Bookworm; this must be done after every MySQL restart")
    memory_tables_parser.add_argument("--force-reload",dest="force",action="store_true",
                                      help="Force reload on all memory tables. Use\
                                      '--skip-reload' for faster execution. On by default\
                                      .")
    memory_tables_parser.add_argument("--skip-reload",dest="force",action="store_false",
                                      help="Don't reload memory tables which have at least\
                                      one entry in them. Significantly faster, but may produce\
                                      bad results if the underlying tables have been\
                                      changed. Good for maintenance, bad for actively updated\
                                      installations.")
    memory_tables_parser.set_defaults(force=False)
    memory_tables_parser.add_argument("--all",action="store_true",default=False,
                                      help="Search for all bookworm installations on\
                                      the server, and reload memory tables for each of them.")


    ########## Clone and run extensions
    extensions_parser = subparsers.add_parser("extension", help="Install Extensions to the current directory")
    extensions_parser.add_argument("url",help="A cloneable url for the extension you want to pul: passed as an argument to 'git clone,' so may be either using the https protocol or the git protocol")


    ########## Clone and run extensions
    extensions_parser = subparsers.add_parser("query", help="Run a query using the Bookworm API")
    extensions_parser.add_argument("APIcall",help="The json-formatted query to be run.")


    ########## Build components
    extensions_parser = subparsers.add_parser("prep", help="Build individual components.", aliases = ['build'])
    extensions_subparsers = extensions_parser.add_subparsers(title="goal", help="The name of the target.", dest="goal")

    # Bookworm prep targets that allow additional args
    catalog_prep_parser = extensions_subparsers.add_parser("preDatabaseMetadata",
                                                           help=getattr(BookwormManager, "preDatabaseMetadata").__doc__)

    word_ingest_parser = extensions_subparsers.add_parser("database_wordcounts",
                                                           help=getattr(BookwormManager, "database_wordcounts").__doc__)
    word_ingest_parser.add_argument("--no-delete", action="store_true", help="Do not delete and rebuild the token tables. Useful for a partially finished ingest.")

    word_ingest_parser.add_argument("--no-reverse-index", action="store_true", help="When creating the table, choose not to index bookid/wordid/counts. This is useful for really large builds. Because this is specified at table creation time, it does nothing with --no-delete or --index-only.")

    word_ingest_parser.add_argument("--no-index", action="store_true", help="Do not re-enable keys after ingesting tokens. Only do this if you intent to manually enable keys or will run this command again.")

    word_ingest_parser.add_argument("--index-only", action="store_true", help="Only re-enable keys. Supercedes other flags.")

    # Bookworm prep targets that don't allow additional args
    for prep_arg in BookwormManager.__dict__.keys():
        extensions_subparsers.add_parser(prep_arg, help=getattr(BookwormManager, prep_arg).__doc__)

    """
    Some special functions
    """

    init_parser = subparsers.add_parser("init",help="Initialize the current directory as a bookworm directory")
    init_parser.add_argument("--force","-f",help="Overwrite some existing files.",default=False,action="store_true")
    init_parser.add_argument("--yes","-y",help="Automatically use default values with no prompts",default=False,action="store_true")


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
    logging.basicConfig(format=FORMAT, level=numeric_level, datefmt="%I:%M:%S")
    logging.info("Info logging enabled.")
    logging.info("Debug logging enabled.")

    # Create the bookworm
    my_bookworm = BookwormManager(args.configuration, args.database)

    # Call the current action with the arguments passed in.
    getattr(my_bookworm,args.action)(args)
