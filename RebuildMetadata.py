import MySQLdb
import re
import sys
import json
import os
from subprocess import call

import ParseDate

#These three libraries define the Bookworm-specific methods.
from CreateDatabase import *
from ImportNewLibrary import *
from WordsTableCreate import WordsTableCreate

# Pull a dbname from command line input.
dbname = sys.argv[1]
dbuser = sys.argv[2]
dbpassword = sys.argv[3]

Bookworm = BookwormSQLDatabase(dbname,dbuser,dbpassword)

print "Parsing the dates to a native format"
ParseDate.DateParser()

"Writing metadata to new catalog file..."
write_metadata(Bookworm.variables)

Bookworm.load_book_list()
Bookworm.create_memory_table_script()
Bookworm.jsonify_data()
Bookworm.create_API_settings()
