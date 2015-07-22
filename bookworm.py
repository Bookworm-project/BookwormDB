#!/usr/bin/env python

import MySQLdb
import re
import sys
import json
import os
import ConfigParser
import argparse
from subprocess import call
import logging

# These four libraries define the Bookworm-specific methods.
from bookworm.MetaParser import *
from bookworm.CreateDatabase import *

# Pull a method from command line input.


def run_arguments():
    """
    Parse the command line arguments and run them.

    I apologize for how ugly and linear this code is: it's not clear to me
    how to write pretty modular code with the argparse module.
    Refactoring pulls welcome.
    """

    parser = argparse.ArgumentParser(description='Build and maintain a Bookworm database.',prog="bookworm.py")
    parser.add_argument("--configuration",help="The name of the configuration file to read options from: by default, 'bookworm.cnf' in the current directory.", default="bookworm.cnf")
    parser.add_argument("--database",help="The name of the bookworm database in MySQL to connect to: by default, read from the active configuration file.", default=None)

    parser.add_argument("--log-level",help="The logging detail to use for errors. Default is 'warning', only significant problems; info gives a fuller record, and 'debug' dumps many MySQL queries, etc.",choices=["warning","info","debug"],type=str.lower,default="warning")

    # Use subparsers to have an action syntax, like git.
    subparsers = parser.add_subparsers(title="action",help='The commands to run with Bookworm',dest="action")


    ############# build #################
    build_parser = subparsers.add_parser("build",description = "Create files",help="""Build up the component parts of a Bookworm. This is a wrapper around `Make`;\
    if you specify something far along the line (for instance, the linechart GUI), it will\
    build all prior files as well.""")

    # Grep out all possible targets from the Makefile
    targets = [re.sub(r":.*\n","",line) for line in open("Makefile") if re.search(r"^[^ $]+:[^=]",line)]
    
    
    build_parser.add_argument("target",help="""The file you want to create: to build a complete bookworm, enter 'all'""",choices = targets)


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
        default="tsv",type=str.lower,choices=["tsv","json"])

    supplement_parser.add_argument("--key",help="""The name of the key. If not specified and input type is TSV, the first column is used.""",default=None)
    supplement_parser.add_argument("--field_descriptions",help="""A description of the new metadata in the format of "field_descriptions.json"; if empty, we'll just guess at some suitable values.""",default=None)

    
    ######### Reload Memory #############
    memory_tables_parser = subparsers.add_parser("reload_memory",help="Reload the memory\
    tables for the designated Bookworm; this must be done after every MySQL restart")
    memory_tables_parser.add_argument("--force-reload",dest="force",action="store_true",
                                      help="Force reload on all memory tables. Use\
                                      '--skip-reload', for faster execution. On by default\
                                      .")
    memory_tables_parser.add_argument("--skip-reload",dest="force",action="store_false",
                                      help="Don't reload memory tables which have at least\
                                      one entry. Significantly faster, but may produce\
                                      bad results if the underlying tables have been\
                                      changed.")
    memory_tables_parser.set_defaults(force=False)
    memory_tables_parser.add_argument("--all",action="store_true",default=False,
                                      help="Search for all bookworm installations on\
                                      the server, and reload memory tables for each of them.")

    extensions_parser = subparsers.add_parser("extension", help="Install Extensions to the current directory")
    extensions_parser.add_argument("url",help="A cloneable url for the extension you want to pul: passed as an argument to 'git clone,' so may be either using the https protocol or the git protocol")

    """
    Some special functions
    """
    # Not yet implemented.
    
    #init_parser = subparsers.add_parser("init",help="Initialize the current directory as a bookworm directory (not yet implemented)")

    # Call the function
    args = parser.parse_args()

    # Set the logging level based on the input.
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    # Create the bookworm 
    my_bookworm = BookwormManager(args.configuration,args.database)

    # Call the current action with the arguments passed in.
    getattr(my_bookworm,args.action)(args)
    

class Extension(object):
    def __init__(self,args):
        self.args = args
        self.dir = "extensions/" + re.sub(".*/","",self.args.url)
        
    def clone_or_pull(self):
        if not os.path.exists(self.dir):
            logging.info("cloning git repo from " + self.args.url)
            subprocess.call(["git","clone",self.args.url,self.dir])
        else:
            logging.info("updating pre-existing git repo at " + self.dir)
            subprocess.Popen(["git","pull"],cwd=self.dir)
            
    def make(self):
        logging.debug("Running make in " + self.dir)
        subprocess.Popen(["make"],cwd=self.dir)
        
# Initiate MySQL connection.
class BookwormManager(object):
    """
    This class is passed some options that tell it the name of the bookworm it's working on;
    some of the methods here are the directly callable as the command line arguments.

    This is what calls the various other bookworm scripts, whether Python or not.
    """
    
    def __init__(self,cnf_file="bookworm.cnf",database=None,user=None,password=None):
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.read([cnf_file])
        # More specific options override the config file
        if database is None:
            self.dbname = config.get("client","database")
        else:
            self.dbname = database
        ## These could also be handled from the command line.
        self.dbuser = config.get("client","user")
        self.dbpassword = config.get("client","password")

    def extension(self,args):
        """
        Creates (or updates) an extension
        """
        if not os.path.exists("extensions"):
            os.makedirs("extensions")
        my_extension = Extension(args)
        my_extension.clone_or_pull()
        my_extension.make()
        
    
    def build(self,args):
        """
        'Build' is currently a wrapper around 'Make'. We could rewrite
        the make function to wrap this if we wanted.
        """
        subprocess.call(["make","database=" + self.dbname,args.target])
    
    def diskMetadata(self):
        print "Parsing field_descriptions.json"
        ParseFieldDescs()
        print "Parsing jsoncatalog.txt"
        ParseJSONCatalog()
        
    def preDatabaseMetadata(self):
        Bookworm = BookwormSQLDatabase()
        print "Writing metadata to new catalog file..."        
        Bookworm.variableSet.writeMetadata()

        # This creates helper files in the /metadata/ folder.

    def metadata(self):
        self.diskMetadata()
        self.preDatabaseMetadata()


    def guessAtFieldDescriptions(self,args):
        Bookworm = BookwormSQLDatabase(self.dbname,variableFile=None)
        Bookworm.setVariables("files/metadata/jsoncatalog.txt",jsonDefinition=None)
        import os
        if not os.path.exists("files/metadata/field_descriptions.json"):
            output = open("files/metadata/field_descriptions.json","w")
            output.write(json.dumps(Bookworm.variableSet.guessAtFieldDescriptions()))
            
    def reload_memory(self,args):
        dbnames = [self.dbname]
        if args.all==True:
            dbnames = []
            datahandler = BookwormSQLDatabase(self.dbname,variableFile=None)
            cursor = datahandler.db.query("SELECT TABLE_SCHEMA FROM information_schema.tables WHERE TABLE_NAME='masterTableTable'")
            for row in cursor.fetchall():
                dbnames.append(row[0])

        for database in dbnames:
            Bookworm = BookwormSQLDatabase(self.dbname,variableFile=None)
            Bookworm.reloadMemoryTables(force=args.force)

    def database_metadata(self):
        Bookworm = BookwormSQLDatabase(self.dbname)
        Bookworm.load_book_list()

        # This creates a table in the database that makes the results of
        # field_descriptions accessible through the API, and updates the
        Bookworm.loadVariableDescriptionsIntoDatabase()

        # This needs to be run if the database resets. It builds a
        # temporary MySQL table and the GUI will not work if this table is not built.
        Bookworm.reloadMemoryTables()

        print "adding cron job to automatically reload memory tables on launch"
        print "(this assumes this machine is the MySQL server, which need not be the case)"

        subprocess.call(["sh","scripts/scheduleCronJob.sh"])

        Bookworm.jsonify_data() # Create the self.dbname.json file in the root directory.
        Bookworm.create_API_settings()

        Bookworm.grantPrivileges()

    def add_metadata(self,args):
        Bookworm=BookwormSQLDatabase(self.dbname,None)

        anchorField = args.key
        if args.format=="tsv":
            # TSV is just converted into JSON in a file at tmp.txt, and slurped in that way.
            if args.key is None:
                anchor = open(args.filename).readline().split("\t")[0]
            convertToJSON(filename)
            args.file="tmp.txt"
        Bookworm.importNewFile(args.file,anchorField=args.key,jsonDefinition=field_descriptions)

    def supplementMetadataFromJSON(self):
        """
        This is a more powerful method to import a json dictionary of the same form
        as jsoncatalog.txt. (More powerful because it lets you use a combination of
        files, arrays instead of single elements, and a specification for each element.)
        """

        if len(sys.argv) > 4:
            #If there are multiple entries for each element, you can specify 'unique'
            # by typing "False" as the last entry.
            field_descriptions = sys.argv.pop()
        else:
            field_descriptions = None
            print "guessing at field descriptions for the import"
        """
        The anchor should be intuited, not named.
        """
        anchor = sys.argv.pop()

        if len(sys.argv)==3:
            filename = sys.argv.pop()
        else:
            print "you must supply exactly one argument to 'addCategoricalFromFile'"
            raise
        Bookworm=BookwormSQLDatabase()
        Bookworm.importNewFile(filename,anchorField=anchor,jsonDefinition=field_descriptions)


    def database_wordcounts(self):
        """
        Builds the wordcount components of the database. This will die
        if you can't connect to the database server.
        """
        Bookworm = BookwormSQLDatabase()
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
        datahandler = BookwormSQLDatabase(self.dbname)
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


if __name__=="__main__":
    run_arguments()
