from __future__ import print_function
import re
from subprocess import call
from subprocess import Popen
import logging
import sys
import os
import bookwormDB
import argparse

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

    This is what calls the various other bookworm scripts, whether Python or not.
    """
    
    def __init__(self,cnf_file=None,database=None,user=None,password=None):
        # This will likely be changed if it isn't None.
        import ConfigParser

        self.basedir = None
        for i in range(10):
            basedir = "../"*i
            if os.path.exists(basedir + ".bookworm"):
                self.basedir = basedir
            if self.basedir==None:
                logging.debug("No bookworm directory found; proceeding on nonetheless.")
        
        self.dbname=database

        if cnf_file is None:
            cnf_file=self.basedir + "/bookworm.cnf"
            
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.read([cnf_file])
        if config.has_section("client"):
            """
            Silently go along if the config doesn't exist.
            """
            self.dbname = config.get("client","database")
            ## These could also be handled from the command line,
            ## but it's such a limit case I'm not yet supporting it.
            self.dbuser = config.get("client","user")
            self.dbpassword = config.get("client","password")

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
            bookwormDB.configuration.reconfigure_passwords(args.users,args.force)
            
    def tokenize(self,args):
        
        import bookwormDB.tokenizer
        
        """
        Handle functions related to tokenization and encoding.
        
        Should eventually be able to accept arguments like "token-regex"
        and already-tokenized documents.
        """
        
        if args.process=="encode":
            if args.feature_counts:
                # Ideally the infile would be described by a specific file location here.
                bookwormDB.tokenizer.encodePreTokenizedStream(infile=sys.stdin,levels=["unigrams"])
                #bookwormDB.tokenizer.encodePreTokenizedStream(sys.stdin,levels=["bigrams"])
            else:
                bookwormDB.tokenizer.encode_text_stream()
            
        if args.process=="text_stream":
            if args.feature_counts:
                logging.error("Can't print the raw text from feature counts.")
                raise
            textfile_locations = ["input.txt",".bookworm/texts/input.txt","../input.txt",".bookworm/texts/raw","input.sh"]
            if args.file is None:
                for file in textfile_locations:
                    if os.path.exists(file):
                        args.file = file
                        break
                if args.file is None:
                    # One of those should have worked.
                    import json
                    raise IOError("Unable to find an input.txt or input.sh file in a default location: those are " + json.dumps(textfile_locations))
            if os.path.isdir(args.file):
                for (root,dirs,files) in os.walk(args.file): 
                    for name in files:
                        path = os.path.join(root,name)
                        content = open(path).read().replace("\n"," ").replace("\t"," ").replace("\r"," ")
                        identity = path.replace(args.file,"").replace(".txt","").strip("/")
                        print(identity + "\t" + content)
            elif os.path.exists(args.file) and (args.file.endswith(".sh")):
                logging.debug("Attempting to print text stream by executing the script at" + args.file)
                Popen(["./" + args.file])
            elif os.path.exists(args.file):
                # I really don't care about useless use of cat here; processor overhead is being lost elsewhere.
                Popen(["cat", args.file])
            else:
                raise IOError("No input file found.")
        if args.process=="token_stream":
            """
            It is currently not possible to tokenize a bookworm-formatted file directly,
            *and* have the ids removed from the start.
            """
            require_id = False
            if args.file is None:
                args.file = sys.stdin
                require_id = True
            else:
                args.file = open(args.file)
            bookwormDB.tokenizer.print_token_stream(args.file,require_ids = require_id)

        if args.process=="word_db":
            import bookwormDB.wordcounter
            """
            Read an endless string of space-delimited characters, and build it into
            a words table.
            """
            if args.feature_counts:
                bookwormDB.wordcounter.write_word_ids_from_feature_counts(sys.stdin)
            else:
                bookwormDB.wordcounter.WordsTableCreate()
            
    def init(self,args):
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
                self.configuration(askk = not args.yes)
            os.makedirs(".bookworm")
        else:
            self.configuration(askk = not args.yes)
        
    def query(self,args):
        """
        Run a query against the API.
        """
        
        from bookwormDB.general_API import SQLAPIcall
        import json
        
        query = json.loads(args.APIcall)
        caller = SQLAPIcall(query)
        print(caller.execute())
        
    def serve(self,args):

        import CGIHTTPServer
        from BaseHTTPServer import HTTPServer
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
        self.build(args)
        
        os.chdir(base_dir)
        # Actually serve it.
        PORT = args.port

        httpd = HTTPServer(("", PORT), CGIHTTPServer.CGIHTTPRequestHandler)

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
        
    def prep(self,args):
        """
        This is a wrapper to all the functions define here: the purpose
        is to continue to allow access to internal methods in, for instance,
        the Makefile, without documenting all of them in separate functions.

        That's a little groaty, I know.
        """
        logging.debug(args)
        getattr(self,args.goal)(cmd_args=args)
        
    def build(self,args):
        """
        'Build' is currently a wrapper around 'Make'. We could rewrite
        the make function to wrap this if we wanted to be more pythonic.
        
        The makefile lives with the rest of the dist code.
        """
        logLevel=logging.getLevelName(logging.getLogger().getEffectiveLevel())
        loc = os.path.dirname(bookwormDB.__file__) + "/etc/" + "bookworm_Makefile"
        logging.debug("Preparing to create " + args.target + " using the makefile at " + loc + "bookworm_Makefile")
        make_args = [
            "make",
            "-f",loc,
            "database=" + self.dbname,
            "logLevel=" + logLevel
            ]
        if args.action == "serve":
            make_args.append("webDirectory=" + args.dir)
        if args.feature_counts:
            make_args.append("maybe_feature_counts=--feature-counts")
        make_args.append(args.target)
        call(make_args)
        
    def diskMetadata(self):
        import bookwormDB.MetaParser
        logging.info("Parsing field_descriptions.json")
        bookwormDB.MetaParser.ParseFieldDescs()
        logging.info("Parsing jsoncatalog.txt")
        bookwormDB.MetaParser.ParseJSONCatalog()
        
    def preDatabaseMetadata(self, cmd_args=None, **kwargs):
        import bookwormDB.CreateDatabase
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase()
        logging.info("Writing metadata to new catalog file...")
        if cmd_args:
            compress = cmd_args.gzip
        else:
            compress = False
        Bookworm.variableSet.writeMetadata(compress=compress)

        # This creates helper files in the /metadata/ folder.

    def text_id_database(self, **kwargs):
        """
        This function is defined in Create Database.
        It builds a file at .bookworm/texts/textids.dbm
        """
        import bookwormDB.CreateDatabase
        bookwormDB.CreateDatabase.text_id_dbm()
        
    def metadata(self, **kwargs):
        self.diskMetadata()
        self.preDatabaseMetadata()

    def catalog_metadata(self, **kwargs):
        from bookwormDB.MetaParser import parse_initial_catalog
        parse_initial_catalog()

    def guessAtFieldDescriptions(self, **kwargs):
        """
        Use a number of rules of thumb to automatically generate a field_descriptions.json file.
        This may bin some categories incorrectly (depending on names, for example it may treat dates
        as either categorical or time variables).
        """
        
        import bookwormDB.CreateDatabase
        import json
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,variableFile=None)
        Bookworm.setVariables("jsoncatalog.txt",jsonDefinition=None)
        import os
        if not os.path.exists("field_descriptions.json"):
            output = open("field_descriptions.json","w")
            output.write(json.dumps(Bookworm.variableSet.guessAtFieldDescriptions()))
        else:
            logging.error("""
            You already have a file at field_descriptions.json
            Dying rather than overwrite it.
            """)
            sys.exit()
            
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

    def configuration(self,askk):
        import bookwormDB.configuration
        bookwormDB.configuration.create(ask_about_defaults=askk)
            
    def database_metadata(self, **kwargs):
        import bookwormDB.CreateDatabase
        logging.debug("creating metadata db")
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname)
        Bookworm.variableSet.loadMetadata()

        logging.debug("creating metadata variable tables")
        # This creates a table in the database that makes the results of
        # field_descriptions accessible through the API, and updates the
        Bookworm.loadVariableDescriptionsIntoDatabase()


        Bookworm.create_fastcat_and_wordsheap_disk_tables()

        # The temporary memory tables are no longer automatically created on a build.
        # To create them, use `bookworm reload_memory`.
        # Bookworm.reloadMemoryTables()

        #print "adding cron job to automatically reload memory tables on launch"
        #print "(this assumes this machine is the MySQL server, which need not be the case)"
        #call(["sh","scripts/scheduleCronJob.sh"])
        Bookworm.jsonify_data() # Create the self.dbname.json file in the root directory.
        Bookworm.create_API_settings()

        Bookworm.grantPrivileges()

    def add_metadata(self, args):
        import bookwormDB.CreateDatabase
        import bookwormDB.convertTSVtoJSONarray
        bookworm=bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,None)
        anchorField = args.key
        if args.format=="tsv":
            # TSV is just converted into JSON in a file at tmp.txt, and slurped in that way.
            if args.key is None:
                args.key = open(args.file).readline().split("\t")[0]
            bookwormDB.convertTSVtoJSONarray.convertToJSON(args.file)
            args.file="tmp.txt"
        bookworm.importNewFile(args.file,
                               anchorField=args.key,
                               jsonDefinition=args.field_descriptions)


    def database_wordcounts(self, cmd_args=None, **kwargs):
        """
        Builds the wordcount components of the database. This will die
        if you can't connect to the database server.
        """
        import bookwormDB.CreateDatabase
        
        index = True
        reverse_index = True
        ingest = True
        newtable = True

        if cmd_args:
            if cmd_args.index_only:
                ingest = False
                newtable = False
            else:
                index = not cmd_args.no_index
                newtable = not cmd_args.no_delete
            reverse_index = not cmd_args.no_reverse_index
            if not (newtable and ingest and index): 
                logging.warn("database_wordcounts args not supported for bigrams yet.")

        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase()
        Bookworm.load_word_list()
        Bookworm.create_unigram_book_counts(newtable=newtable, ingest=ingest, index=index, reverse_index=reverse_index)
        Bookworm.create_bigram_book_counts()

    def database(self):
        self.database_wordcounts()
        self.database_metadata()

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
        logging.debug("Running make in " + self.dir)
        Popen(["make"],cwd=self.dir)
 
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


    parser.add_argument("--feature-counts",action="store_true",default=False,
                                 help="Use pre-calculated feature counts rather than tokenizing complete text on the fly. Off by default")

    parser.add_argument("--ngrams",nargs="+",default=["unigrams","bigrams"],help="What levels to parse with. Multiple arguments should be unquoted in spaces. This option currently does nothing.")

    
    # Use subparsers to have an action syntax, like git.
    subparsers = parser.add_subparsers(title="action",help='The commands to run with Bookworm',dest="action")


    ############# build #################
    build_parser = subparsers.add_parser("build",description = "Create files",help="""Build up the component parts of a Bookworm.\
    This is a wrapper around `Make`;\
    if you specify something far along the line (for instance, the linechart GUI), it will\
    build all prior files as well.""")
    
    build_parser.add_argument("target",help="The make that you want to build. To build a full bookworm, type 'build all'. To destroy your bookworm, type 'build pristine'")

    # Grep out all possible targets from the Makefile

    ############# supplement #################
    supplement_parser = subparsers.add_parser("add_metadata",help="""Supplement the\
    metadata with new items. They can be keyed to any field already in the database.""")
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

    
    ### Handle tokenization and wordcounts and encode
    tokenization_parser = subparsers.add_parser("tokenize", help="tokenize (and optionally, encode) text. Currently requires a stream to stdin as input.")
    
    tokenization_subparsers = tokenization_parser.add_subparsers(title="process",help='The part of the subparser to run: see help for more details.',dest="process")
    encode_parser = tokenization_subparsers.add_parser("encode",
                                     help="Encode according to the stored numeric IDs.")
    text_stream_parser = tokenization_subparsers.add_parser("text_stream",
                                                            help="Print text from various sources to stdout in a standard form.")
    text_stream_parser.add_argument("--file","-f",help="location of a formatted input file: leave blank for sensible defaults as described in the documentation.",default=None)
    
    token_stream_parser = tokenization_subparsers.add_parser("token_stream",
        help="Turn text into space-delimited tokens using a regular expression.  use options ")
    token_stream_parser.add_argument("--token-regex",
        help="Regular expression defining tokens. Not currently implemented")
    token_stream_parser.add_argument("--file","-f",
        help="A file to tokenize. By default, reads the output of text_stream from stdin.",
        default=None)

    word_db_parser = tokenization_subparsers.add_parser("word_db",help="Turn a list of tokens into a sorted set of number IDs, even if there are more distinct types than can fit in memory, by writing to disk.")
    ########## Build components
    extensions_parser = subparsers.add_parser("prep", help="Build individual components: primarily used by the Makefile.")
    extensions_subparsers = extensions_parser.add_subparsers(title="goal", help="The name of the target.", dest="goal")

    # Bookworm prep targets that allow additional args
    catalog_prep_parser = extensions_subparsers.add_parser("preDatabaseMetadata",
                                                           help=getattr(BookwormManager, "preDatabaseMetadata").__doc__)
    catalog_prep_parser.add_argument("--gzip", action="store_true", help="Output a compressed catalog file. Only useful for manual needs currently, as later processes still require a decompressed file.")
    
    word_ingest_parser = extensions_subparsers.add_parser("database_wordcounts",
                                                           help=getattr(BookwormManager, "database_wordcounts").__doc__)
    word_ingest_parser.add_argument("--no-delete", action="store_true", help="Do not delete and rebuild the token tables. Useful for a partially finished ingest.")
    word_ingest_parser.add_argument("--no-reverse-index", action="store_true", help="When creating the table, choose not to index bookid/wordid/counts. This is useful for really large builds. Because this is specified at table creation time, it does nothing with --no-delete or --index-only.")
    word_ingest_parser.add_argument("--no-index", action="store_true", help="Do not re-enable keys after ingesting tokens. Only do this if you intent to manually enable keys or will run this command again.")
    word_ingest_parser.add_argument("--index-only", action="store_true", help="Only re-enable keys. Supercedes other flags.")
    # Bookworm prep targets that don't allow additional args
    for prep_arg in ['text_id_database', 'catalog_metadata', 'database_metadata', 'guessAtFieldDescriptions']:
        extensions_subparsers.add_parser(prep_arg, help=getattr(BookwormManager, prep_arg).__doc__)

    """
    Some special functions
    """
    
    init_parser = subparsers.add_parser("init",help="Initialize the current directory as a bookworm directory")
    init_parser.add_argument("--force","-f",help="Overwrite some existing files.",default=False,action="store_true")
    init_parser.add_argument("--yes","-y",help="Automatically use default values with no prompts",default=False,action="store_true")    


    # Serve the current bookworm
    serve_parser = subparsers.add_parser("serve",help="Launch a webserver on the current bookworm. This is much easier than configuring apache, but considerably less secure.")
    serve_parser.add_argument("--port","-p",default="8005",help="The port over which to serve the bookworm",type=int)
    serve_parser.add_argument("--dir","-d",default="http_server",help="A filepath for a directory to serve from. Will be created if it does not exist.")
    
    # Configure the global server.
    configure_parser = subparsers.add_parser("config",help="Some helpers to configure a running bookworm, or to manage your server-wide configuration.")
    configure_parser.add_argument("target",help="The thing you want help configuring.",choices=["mysql"])
    configure_parser.add_argument("--users",nargs="+",choices=["admin","global","root"],help="The user levels you want to act on.",default=["admin","global"])
    configure_parser.add_argument("--force","-f",help="Overwrite existing configurations in potentially bad ways.",action="store_true",default=False)

    # Call the function
    args = parser.parse_args()
    # Set the logging level based on the input.
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    # While we're at it, log with line numbers
    FORMAT = "[%(filename)s:%(lineno)s-%(funcName)s()] %(message)s"
    logging.basicConfig(format=FORMAT, level=numeric_level)
    logging.info("Info logging enabled.")
    logging.info("Debug logging enabled.")

    # Create the bookworm 
    my_bookworm = BookwormManager(args.configuration,args.database)

    # Call the current action with the arguments passed in.
    getattr(my_bookworm,args.action)(args)
    
