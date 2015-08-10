import re
from subprocess import call
from subprocess import Popen
import logging
import sys
import os
import bookwormDB

"""
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
    
    def __init__(self,cnf_file="bookworm.cnf",database=None,user=None,password=None):
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
            import bookwormDB.fix_config 
            bookwormDB.fix_config.reconfigure_passwords(args.users,args.force)
            
    def tokenize(self,args):
        
        import bookwormDB.tokenizer
        
        """
        Handle functions related to tokenization and encoding.
        
        Should eventually be able to accept arguments like "token-regex"
        and already-tokenized documents.
        """

        
        if args.process=="encode":
            bookwormDB.tokenizer.encode_text_stream()
        
        if args.process=="text_stream":
            if args.file is None:
                for file in ["input.txt",".bookworm/texts/input.txt","../input.txt",".bookworm/texts/raw","input.sh"]:
                    if os.path.exists(file):
                        args.file = file
                        break
                if args.file is None:
                    # One of those should have worked.
                    raise IOError("Unable to find an input.txt or input.sh file in a default location")
            
            if os.path.isdir(args.file):
                for (root,dirs,files) in os.walk(args.file): 
                    for name in files:
                        path = os.path.join(root,name)
                        content = open(path).read().replace("\n"," ").replace("\t"," ").replace("\r"," ")
                        identity = path.replace(args.file,"").replace(".txt","").strip("/")
                        print identity + "\t" + content
            elif os.path.exists(args.file) and (args.file.endswith(".sh")):
                logging.debug("Attempting to print text stream by executing " + args.file)
                Popen(["./" + args.file])
            elif os.path.exists(args.file):
                # I really don't care about useless use of cat here; processor overhead is being lost elsewhere.
                Popen(["cat", args.file])
            else:
                raise IOError("No input file found.")
        if args.process=="token_stream":
            bookwormDB.tokenizer.print_token_stream()

        if args.process=="word_db":
            import bookwormDB.wordcounter
            """
            Read an endless string of space-delimited characters, and 
            """
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
                self.configuration()
            os.makedirs(".bookworm")
        else:
            self.configuration()
        
        """
        UPDATE--This section blocked out:
        trying a new strategy of just running the code from inside the python dir.
        
        Hardcoding the files we need right here. Not the prettiest solution:
        should potentially just copy the whole tree to the current dir.

        import shutil
        loc = os.path.dirname(bookwormDB.__file__) + "/etc/"

        needed_files={"bookworm_Makefile":"bookworm_Makefile"}
        
        for key,val in needed_files.iteritems():
            src = loc + key
            dst = val
            newdir = os.path.dirname(dst)
            if not os.path.exists(newdir) and newdir != "":
                # Create dir if not exists.
                os.makedirs(os.path.dirname(dst))
            shutil.copyfile(src, dst)
        """

    def query(self,args):
        """
        Run a query against the API.
        """
        
        from bookwormDB.general_API import SQLAPIcall
        import json
        
        query = json.loads(args.APIcall)
        caller = SQLAPIcall(query)
        print caller.execute()
        
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

        print "\n\n" + "****"*20
        print "A local bookworm server is now running"
        print "You can now view some charts in a web-browser at http://localhost:%d/D3" % PORT
        print "If you have a time variable, linecharts are at http://localhost:%d/%s" % (PORT,self.dbname)
        print "Please note that this is not a very secure way: if you plan to put your bookworm"
        print "on the open web, consider using apache."
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
        getattr(self,args.goal)()
        
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
            
        make_args.append(args.target)
        call(make_args)
        
    def diskMetadata(self):
        import bookwormDB.MetaParser
        logging.info("Parsing field_descriptions.json")
        bookwormDB.MetaParser.ParseFieldDescs()
        logging.info("Parsing jsoncatalog.txt")
        bookwormDB.MetaParser.ParseJSONCatalog()
        
    def preDatabaseMetadata(self):
        import bookwormDB.CreateDatabase
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase()
        logging.info("Writing metadata to new catalog file...")
        Bookworm.variableSet.writeMetadata()

        # This creates helper files in the /metadata/ folder.

    def text_id_database(self):
        """
        This function is defined in Create Database.
        It builds a file at .bookworm/texts/textids.dbm
        """
        import bookwormDB.CreateDatabase
        bookwormDB.CreateDatabase.text_id_dbm()
        
    def metadata(self):
        self.diskMetadata()
        self.preDatabaseMetadata()

    def catalog_metadata(self):
        from bookwormDB.MetaParser import parse_initial_catalog
        parse_initial_catalog()

    def guessAtFieldDescriptions(self):
        import bookwormDB.CreateDatabase
        import json

        
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,variableFile=None)
        Bookworm.setVariables(".bookworm/metadata/jsoncatalog.txt",jsonDefinition=None)
        import os
        if not os.path.exists(".bookworm/metadata/field_descriptions.json"):
            output = open(".bookworm/metadata/field_descriptions.json","w")
            output.write(json.dumps(Bookworm.variableSet.guessAtFieldDescriptions()))
        else:
            logging.error("""
            You already have a file at .bookworm/metadata/field_descriptions.json
            Dying rather than overwrite it.
            """)
            exit
            
    def reload_memory(self,args):
        import bookwormDB.CreateDatabase
        dbnames = [self.dbname]
        if args.all==True:
            dbnames = []
            datahandler = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,variableFile=None)
            cursor = datahandler.db.query("SELECT TABLE_SCHEMA FROM information_schema.tables WHERE TABLE_NAME='masterTableTable'")
            for row in cursor.fetchall():
                dbnames.append(row[0])
            logging.debug("Reloading the following tables:")
            logging.debug(dbnames)

        for database in dbnames:
            logging.debug("Reloading memory tables for %s" %database)
            Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(database,variableFile=None)
            Bookworm.reloadMemoryTables(force=args.force)

    def configuration(self):
        import bookwormDB.configuration
        bookwormDB.configuration.create()
            
    def database_metadata(self):
        import bookwormDB.CreateDatabase

        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname)
        Bookworm.load_book_list()

        # This creates a table in the database that makes the results of
        # field_descriptions accessible through the API, and updates the
        Bookworm.loadVariableDescriptionsIntoDatabase()

        # This needs to be run if the database resets. It builds a
        # temporary MySQL table and the GUI will not work if this table is not built.
        Bookworm.reloadMemoryTables()

        #print "adding cron job to automatically reload memory tables on launch"
        #print "(this assumes this machine is the MySQL server, which need not be the case)"
        #call(["sh","scripts/scheduleCronJob.sh"])

        Bookworm.jsonify_data() # Create the self.dbname.json file in the root directory.
        Bookworm.create_API_settings()

        Bookworm.grantPrivileges()

    def add_metadata(self,args):
        import bookwormDB.CreateDatabase
        import bookwormDB.convertTSVtoJSONarray
        bookworm=bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname,None)
        anchorField = args.key
        if args.format=="tsv":
            # TSV is just converted into JSON in a file at tmp.txt, and slurped in that way.
            if args.key is None:
                anchor = open(args.file).readline().split("\t")[0]
            bookwormDB.convertTSVtoJSONarray.convertToJSON(args.file)
            args.file="tmp.txt"
        bookworm.importNewFile(args.file,
                               anchorField=args.key,
                               jsonDefinition=args.field_descriptions)


    def database_wordcounts(self):
        """
        Builds the wordcount components of the database. This will die
        if you can't connect to the database server.
        """
        import bookwormDB.CreateDatabase
        import ConfigParser
        
        Bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase()
        Bookworm.load_word_list()
        Bookworm.create_unigram_book_counts()
        Bookworm.create_bigram_book_counts()


    def database(self):
        self.database_wordcounts()
        self.database_metadata()

    def doctor(self):
        """
        Do some things to update old databases to the newest version.
        This should always be safe to run, but may do more than diagnostics.
        """
        import bookwormDB.CreateDatabase
        import ConfigParser


        datahandler = bookwormDB.CreateDatabase.BookwormSQLDatabase(self.dbname)
        cursor = datahandler.db.query("CREATE DATABASE IF NOT EXISTS bookworm_scratch")
        cursor = datahandler.db.query("GRANT ALL ON bookworm_scratch.* TO '%s'@'localhost' IDENTIFIED BY '%s'" %(self.dbuser,self.dbpassword))
        #Just to be safe
        cursor = datahandler.db.query("GRANT ALL ON bookworm_scratch.* TO '%s'@'127.0.0.1' IDENTIFIED BY '%s'" %(self.dbuser,self.dbpassword))
        cursor = datahandler.db.query("FLUSH PRIVILEGES")
        cursor = datahandler.db.query("DROP TABLE IF EXISTS bookworm_scratch.cache")
        cursor = datahandler.db.query("""CREATE TABLE bookworm_scratch.cache (
        fieldname VARCHAR(90) NOT NULL, PRIMARY KEY (fieldname),
        created TIMESTAMP,
        modified TIMESTAMP,
        createCode VARCHAR(15845),
        data BLOB,
        count INT NOT NULL) ENGINE=InnoDB""")

        """
        check some MySQL settings
        """

        config = ConfigParser.ConfigParser(allow_no_value=True)
        read = config.read(["/.my.cnf","~/my.cnf","/etc/mysql/my.cnf","/etc/my.cnf"])
        if len(read) == 0:
            sys.stderr.write("Warning: couldn't find a my.cnf file in the usual places ('/etc/my.cnf' and /etc/mysql/my.cnf.' To see if your settings are OK, you'll have to search for this method and change the code just above it.")
        try:
            print config.get("mysqld","query_cache_size") + config.get("mysqld","query_cache_type") + config.get("mysqld","query_cache_limit")
        except:
            sys.stderr.write("Warning: Your my.cnf file doesn't properly specify all three query cache values: perhaps you need to run or re-run etc/mysqlsetup/updateMyCnf.py, or insert the defaults in there by hand? Recent versions of MySQL have different default settings that may break things.\n")

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
