#!/usr/bin/env python

import MySQLdb
import re
import sys
import json
import os
import ConfigParser
from subprocess import call

# These four libraries define the Bookworm-specific methods.
from bookworm.MetaParser import *
from bookworm.CreateDatabase import *

# Pull a dbname from command line input.
try:
    methods = sys.argv[1:]
    
except IndexError:
    print """Give as a command argument one of the following:
    metadata
    wordcounts
    database
    Doing all of them.
    """
    methods = ["metadata","wordcounts","database"]

#Use the client listed in the my.cnf file for access

config = ConfigParser.ConfigParser(allow_no_value=True)
config.read(["bookworm.cnf"])
dbuser = config.get("client","user")
dbpassword = config.get("client","password")
dbname = config.get("client","database")

# Initiate MySQL connection.
class oneClickInstance(object):
    #The instance has methods corresponding to what you want to make: they should be passed in, in the order you want them
    #to be run.

    def __init__(self):
        pass
    
    def metadata(self):
        print "Parsing field_descriptions.json"
        ParseFieldDescs()
        print "Parsing jsoncatalog.txt"
        ParseJSONCatalog()
        Bookworm = BookwormSQLDatabase()

        # This creates helper files in the /metadata/ folder.
        print "Writing metadata to new catalog file..."
        Bookworm.variableSet.writeMetadata()

    def database_metadata(self):
        Bookworm = BookwormSQLDatabase(dbname)
        Bookworm.load_book_list()

        # This creates a table in the database that makes the results of
        # field_descriptions accessible through the API, and updates the 
        Bookworm.loadVariableDescriptionsIntoDatabase()

        # This needs to be run if the database resets. It builds a
        # temporary MySQL table and the GUI will not work if this table is not built.
        Bookworm.create_memory_table_script()

        print "adding cron job to automatically reload memory tables on launch"
        print "(this assumes this machine is the MySQL server, which need not be the case)"

        subprocess.call(["sh","scripts/scheduleCronJob.sh"])

        Bookworm.jsonify_data() # Create the dbname.json file in the root directory.
        Bookworm.create_API_settings()
        
    def addCategoricalFromFile(self):
        """
        Reads a categorical variable from a .tsv file.
        First column is an existing anchor:
        Second column is the new data that's being inserted.
        That file MUST have as its first row.
        """
        if len(sys.argv) > 3:
            unique = eval(sys.argv.pop())
        else:
            unique = True

        if len(sys.argv)==3:
            file = sys.argv.pop()
        else:
            print "you must supply exactly one argument to 'addCategoricalFromFile'"
        #If it's not unique to the key, you need to pass "False" as an argument.

        
        Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword,readVariableFile=False)
        Bookworm.addCategoricalFromFile(file,unique=unique)


    def database_wordcounts(self):
        Bookworm = BookwormSQLDatabase()
        Bookworm.load_word_list()
        Bookworm.create_unigram_book_counts()
        Bookworm.create_bigram_book_counts()

    def database(self):
        self.database_wordcounts()
        self.database_metadata()


if __name__=="__main__":
    program = oneClickInstance()
    for method in methods:
        getattr(program,method)()
