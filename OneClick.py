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
from bookworm.WordsTableCreate import *
from bookworm.tokenizeAndEncodeFiles import bookidlist


# Pull a dbname from command line input.
try:
    dbname = sys.argv[1]
except:
    print "You must give the name of the Bookworm you wish to create"
    raise

#Use the client listed in the my.cnf file for access
systemConfigFile = ConfigParser.ConfigParser(allow_no_value=True)
systemConfigFile.read(["/etc/mysql/my.cnf"]);
dbuser = systemConfigFile.get("client","user")
dbpassword = systemConfigFile.get("client","password")

Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)

print "Parsing field_descriptions.json"
ParseFieldDescs()
print "Parsing jsoncatalog.json"
ParseJSONCatalog()

# Initiate MySQL connection.


# This creates helper files in the /metadata/ folder.
print "Writing metadata to new catalog file..."
write_metadata(Bookworm.variables)

# These are imported with ImportNewLibrary
CopyDirectoryStructuresFromRawDirectory()


bookidList = bookidlist()

#These next three steps each take quite a while, but less than they used to.
bookidList.createUnigramsAndBigrams()

print "Creating a master wordlist"
WordsTableCreate(maxDictionaryLength=1000000,maxMemoryStorage = 15000000)

bookidList.encodeAll()

Bookworm.load_word_list()
Bookworm.create_unigram_book_counts()
Bookworm.create_bigram_book_counts()
Bookworm.load_book_list()

# This needs to be run if the database resets. It builds a temporary MySQL table and the GUI will not work if this table is not built.
Bookworm.create_memory_table_script()


#This creates a table in the database that makes the results of field_descriptions accessible through the API.
Bookworm.loadVariableDescriptionsIntoDatabase()


print "adding cron job to automatically reload memory tables on launch"
print "(this assumes this machine is the MySQL server, which need not be the case)"

subprocess.call(["sh","scripts/scheduleCronJob.sh"])

Bookworm.jsonify_data() # Create the dbname.json file in the root directory.
Bookworm.create_API_settings()
