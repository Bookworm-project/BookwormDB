import MySQLdb
import re
import sys
import json
import os
from subprocess import call

#This is a temporary clone of ImportNewDatabase.py that doesn't touch the words tables (which are the ones that take the longest to build)

#These three libraries define the Bookworm-specific methods.
from CreateDatabase import *
from ImportNewLibrary import *
from WordsTableCreate import WordsTableCreate

#First off: what are we using? Pull a dbname from command line input.                                                                 
#As well as the username and password. 
dbname = sys.argv[1]
dbuser = sys.argv[2]
dbpassword = sys.argv[3]

Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)


print "Parsing the dates to a native format"
#This should be brought into the modular fold.
call(['python','ParseDate.py',dbname])

"Writing metadata to new catalog file..."

write_metadata(Bookworm.variables)

#These are imported with ImportNewLibrary
#CopyDirectoryStructuresFromRawDirectory()

#CleanTexts()
#MakeUnigramCounts()
#MakeBigramCounts()
#MakeTrigramCounts() #Doesn't do nothing yet.

#print "Creating a master wordlist" #These values shouldn't be hard-coded in, probably:
#WordsTableCreate(maxDictionaryLength=1000000,maxMemoryStorage = 15000000)



#EncodeUnigrams()
#EncodeBigrams()


"""
Most of these commands are inside CreateNewDatabase.py. For manual constructions or 
stop-and-start operations, it's very helpful to have them spread out like this.
The class initialization should be quick, but does create a database if it's not there.
"""

#Bookworm.load_word_list()
#Bookworm.create_unigram_book_counts()
#Bookworm.create_bigram_book_counts()
Bookworm.load_book_list()
Bookworm.create_memory_table_script()
Bookworm.jsonify_data()
Bookworm.create_API_settings()
