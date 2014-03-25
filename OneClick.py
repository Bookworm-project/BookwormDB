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
    dbname = sys.argv[1]

except:
    print "You must give the name of the Bookworm you wish to create"
    raise

try: 
    methods = sys.argv[2:]
except IndexError:
    print """Give as a command argument one of the following:
    metadata
    wordcounts
    database
    Doing all of them.
    """
    methods = ["metadata","wordcounts","database"]

#Use the client listed in the my.cnf file for access

systemConfigFile = ConfigParser.ConfigParser(allow_no_value=True)

try:
    systemConfigFile.read(["/etc/mysql/my.cnf"]);
    #The error isn't thrown until you try to read the damned thing,
    #So we just try that here.
    dbuser = systemConfigFile.get("client","user")

except:
    #It's here on my Mac. But doing this could get ugly as we try for more
    #over time.
    systemConfigFile.read(["/etc/my.cnf"])

dbuser = systemConfigFile.get("client","user")
dbpassword = systemConfigFile.get("client","password")

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
        Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)

        # This creates helper files in the /metadata/ folder.
        print "Writing metadata to new catalog file..."
        write_metadata(Bookworm.variables)

    def database_metadata(self):
        Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)
        Bookworm.load_book_list()

        #This creates a table in the database that makes the results of field_descriptions accessible through the API.
        Bookworm.loadVariableDescriptionsIntoDatabase()

        # This needs to be run if the database resets. It builds a temporary MySQL table and the GUI will not work if this table is not built.
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
        file = sys.argv[3]
        #If it's not unique to the key, you need to pass "False" as an argument.
        if len(sys.argv) > 4:
            unique = eval(sys.argv[4])
        else:
            unique = True
        
        Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword,readVariableFile=False)
        Bookworm.addCategoricalFromFile(file,unique=unique)


    def database_wordcounts(self):
        Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)
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
