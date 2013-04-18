import MySQLdb
import re
import sys
import json
import os
from subprocess import call

# These four libraries define the Bookworm-specific methods.
from bookworm.MetaParser import *
from bookworm.CreateDatabase import *
from bookworm.WordsTableCreate import *
from bookworm.tokenizeAndEncodeFiles import bookidlist


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

# These are imported with ImportNewLibrary
CopyDirectoryStructuresFromRawDirectory()
bookidList = bookidlist()
bookidList.clean()
bookidList.tokenize('unigrams')
bookidList.tokenize('bigrams')
#bookidList.tokenize('trigrams')

print "Creating a master wordlist"
WordsTableCreate(maxDictionaryLength=1000000,maxMemoryStorage = 15000000)
bookidList.encodeUnigrams()
bookidList.encodeBigrams()

Bookworm.load_word_list()
Bookworm.create_unigram_book_counts()
Bookworm.create_bigram_book_counts()
Bookworm.load_book_list()

# This needs to be run if the database resets. It builds a temporary MySQL table and the GUI will not work if this table is not built.
Bookworm.create_memory_table_script()

Bookworm.jsonify_data() # Create the dbname.json file in the root directory.
Bookworm.create_API_settings()
