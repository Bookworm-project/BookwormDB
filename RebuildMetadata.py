import MySQLdb
import re
import sys
import json
import os
from subprocess import call

from ParseDate import *
from CreateDatabase import *
from ImportNewLibrary import *
from WordsTableCreate import WordsTableCreate

# Pull a dbname from command line input.
dbname = sys.argv[1]
dbuser = sys.argv[2]
dbpassword = sys.argv[3]

Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)

print "Parsing field_descriptions.json"
ParseFieldDescs()

print "Parsing jsoncatalog.json"
ParseJSONCatalog()

"Writing metadata to new catalog file..."
write_metadata(Bookworm.variables)

Bookworm.load_book_list()
Bookworm.create_memory_table_script()
Bookworm.jsonify_data()
Bookworm.create_API_settings()
