import MySQLdb
import re
import sys
import json
import os
from subprocess import call

# These five libraries define the Bookworm-specific methods.
from ParseDate import ParseFieldDescs,ParseJSONCatalog
from CreateDatabase import *
from WordsTableCreate import *
from tokenizeAndEncodeFiles import bookidlist

# Pull a dbname from command line input.
dbname = sys.argv[1]
dbuser = sys.argv[2]
dbpassword = sys.argv[3]

print "Parsing field_descriptions.json"
ParseFieldDescs()

print "Parsing jsoncatalog.json"
ParseJSONCatalog()

# Initiate MySQL connection.
Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)

# This creates helper files in the /metadata/ folder.
print "Writing metadata to new catalog file..."
write_metadata(Bookworm.variables)

#These are imported with ImportNewLibrary
CopyDirectoryStructuresFromRawDirectory() # rsync is very slow when the number of files in /texts/raw/ is large (1000000+)
bookidList = bookidlist()
bookidList.clean()
bookidList.tokenize('unigrams')
bookidList.tokenize('bigrams')
#bookidList.tokenize('trigrams')
print "Creating a master wordlist"
WordsTableCreate(maxDictionaryLength=1000000,maxMemoryStorage = 15000000)
bookidList.encodeUnigrams()
bookidList.encodeBigrams()
#bookidList.encodeTrigrams()


# Most of these commands are inside /Presidio/CreateNewDatabase.py.
Bookworm.load_word_list()
Bookworm.create_unigram_book_counts()
Bookworm.create_bigram_book_counts()
Bookworm.load_book_list()

# This needs to be run if the database resets. It builds a temporary MySQL table and the GUI will not work if this table not built.
Bookworm.create_memory_table_script()

# Create the dbname.json file in the root directory. Move this to the $project/dbname/static/ folder of the web server.
Bookworm.jsonify_data()

Bookworm.create_API_settings()
