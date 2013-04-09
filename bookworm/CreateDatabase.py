#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import MySQLdb
import re
import sys
import json
import os
import decimal

	
class DB:

    def __init__(self, dbname):
        self.dbname = dbname
        self.conn = None

    def connect(self):
        #These scripts run as the Bookworm _Administrator_ on this machine.
        self.conn = MySQLdb.connect(read_default_file="~/.my.cnf", use_unicode='True', charset='utf8', db='', local_infile=1)
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS %s" % self.dbname)
        #Don't use native query attribute here to avoid infinite loops
        cursor.execute("SET NAMES 'utf8'")
        cursor.execute("SET CHARACTER SET 'utf8'")
        cursor.execute("SET storage_engine=MYISAM")
        cursor.execute("USE %s" % self.dbname)

    def query(self, sql):
        """
        Billy defined a separate query method here so that the common case of a connection being
        timed out doesn't cause the whole shebang to fall apart: instead, it just reboots
        the connection and starts up nicely again.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql)
        return cursor


class dataField:
    """
    This define a class that supports a data field from a json definition.
    We'll use this to spit out appropriate sql code and JSON objects where needed.
    The 'definition' here means the user-generated array (submitted in json but 
    parsed out before this) described in the Bookworm interface.
    This knows whether it's unique, whether it should treat itself as a date, and so forth.
    """
    def __init__(self, definition, dbToPutIn, anchorType="MEDIUMINT", anchor="bookid"):
        #anchorType should be derived from somewhere.
        self.anchorType = anchorType
        self.anchor = anchor

        for key in definition.iterkeys():
            vars(self)[key] = definition[key]
        self.dbToPutIn = dbToPutIn

        #The table it's stored in will be either 'catalog', or a new table named after the variable. For now, at least. (later the anchor should get used).

        self.fastField = self.field
        if self.datatype == "categorical":
            self.type = "character"
            #This will catch a common sort of mistake, but also coerce any categorical data to have fewer than 255 characters.
            self.fastField = "%s__id" % self.field

        if self.unique:
            self.table = "catalog"
            self.fasttab = "fastcat"

        else:
            self.table = self.field + "Disk"
            self.fasttab = self.field
            self.outputloc = "files/metadata/%s.txt" % self.field

    def slowSQL(self, withIndex=False):
        #This returns something like """author VARCHAR(255)""", a small definition string with an index, potentially.
        mysqltypes = {
                      "character": "VARCHAR(255)",
                      "integer": "INT",
                      "text": "VARCHAR(5000)",
                      "decimal": "DECIMAL (9,4)"
                     }
        indexstring = ", INDEX (%(field)s), INDEX (%(anchor)s, %(field)s " % self.__dict__
        #need to specify fixed prefix length on text strings: (http://dev.mysql.com/doc/refman/5.0/en/create-index.html)
        indextypes = {
                      "character": "%s)" % indexstring,
                      "integer": "%s)" % indexstring,
                      "text": "%s (255) )" % indexstring,
                      "decimal": "%s)" % indexstring
                     } 
        createstring = " %s %s" % (self.field, mysqltypes[self.type])
        if withIndex and self.type != 'text':
            return '%s%s' % (createstring, indextypes[self.type])
        return createstring

    def fastSQL(self):
        #This creates code to go in a memory table: it assumes that the disk tables are already there, and that a connection cursor is active.
        #Memory tables DON'T SUPPORT VARCHAR (not at a good rate); thus, it has to be stored this other way
        
        if self.datatype != 'etc':
            if self.type == "character":
                self.setIntType()
                return " %(field)s__id %(intType)s" % self.__dict__
            if self.type == "integer":
                return " %s INT" % self.field
            if self.type == "decimal":
                return " %s DECIMAL (9,4) " % self.field
            else:
                return None
        else:
            return None

    def fastLookupTableIfNecessary(self, engine="MEMORY"):

        """
        This uses the already-created ID table to create a memory lookup.
        """
        self.engine = engine
        if self.datatype == 'categorical':
            self.setIntType()
            self.maxlength = self.dbToPutIn.query("SELECT MAX(CHAR_LENGTH(%(field)s)) FROM %(field)s__id" % self.__dict__)
            self.maxlength = self.maxlength.fetchall()[0][0]
            self.maxlength = max([self.maxlength,1])
            return("""DROP TABLE IF EXISTS tmp;
                   CREATE TABLE tmp (%(field)s__id %(intType)s ,PRIMARY KEY (%(field)s__id),
                         %(field)s VARCHAR (%(maxlength)s) ) ENGINE=%(engine)s 
                    SELECT %(field)s__id,%(field)s FROM %(field)s__id;
                   DROP TABLE IF EXISTS %(field)sLookup;
                   RENAME TABLE tmp to %(field)sLookup;
                   """ % self.__dict__)
        return ""

    def fastSQLTable(self,engine="MEMORY"):
        #setting engine to another value will create these tables on disk.
        returnt = ""
        self.engine = engine
        if self.unique:
            pass #when it has to be part of a larger set
        if not self.unique and self.datatype == 'categorical':
            self.setIntType()
            returnt = returnt+"""## Creating the memory storage table for %(field)s
                   DROP TABLE IF EXISTS tmp;
                   CREATE TABLE tmp (%(anchor)s %(anchorType)s , INDEX (%(anchor)s),%(field)s__id %(intType)s ) ENGINE=%(engine)s;
                   INSERT INTO tmp SELECT %(anchor)s ,%(field)s__id FROM %(field)s__id JOIN %(field)sDisk USING (%(field)s);
                   DROP TABLE IF EXISTS %(field)sheap;
                   RENAME TABLE tmp TO %(field)sheap;      
                   """ % self.__dict__
        if self.datatype == 'categorical' and self.unique:
            pass
        return returnt

    def jsonDict(self):
        """
        #This builds a JSON dictionary that can be loaded into outside bookworm in the "options.json" file.
        It's probably a bad design decision, but we can live with it: in the medium-term, all this info
        should just be loaded directly from the database somehow.
        """
        mydict = dict()
        #It gets confusingly named: "type" is the key for real name ("time", "categorical" in the json), but also the mysql key ('character','integer') here. That would require renaming code in a couple places.
        mydict['type'] = self.datatype
        mydict['dbfield'] = self.field
        try:
            mydict['name'] = self.name
        except:
            mydict['name'] = self.field
        if self.datatype == "etc" or self.type == "text":
            return dict() #(Some things don't go into the fast settings because they'd take too long)
        if self.datatype == "time":
            mydict['unit'] = self.field
            #default to the full min and max date ranges
            #times may not be zero or negative
            cursor = self.dbToPutIn.query("SELECT MIN(" + self.field + "), MAX(" + self.field + ") FROM catalog WHERE " + self.field + " > 0 ")
            results = cursor.fetchall()[0]
            mydict['range'] = [results[0], results[1]]
            mydict['initial'] = [results[0], results[1]]
    
        if self.datatype == "categorical":
            mydict['dbfield'] = self.field + "__id"
            #Find all the variables used more than 20 times from the database, and build them into something json-usable.
            cursor = self.dbToPutIn.query("SELECT %(field)s, %(field)s__id  FROM %(field)s__id WHERE %(field)s__count > 20 ORDER BY %(field)s__id ASC LIMIT 500;" % self.__dict__)
            sort_order = []
            descriptions = dict()
            for row in cursor.fetchall():
                code = row[1]
                name = row[0]
                code = to_unicode(code)
                sort_order.append(code)
                descriptions[code] = dict()
                """
                These three things all have slightly different meanings:
                the english name, the database code for that name, and the short display name to show.
                It would be worth allowing lookup files for these: for now, they are what they are and can be further improved by hand.
                """
                descriptions[code]["dbcode"] = code
                descriptions[code]["name"] = name
                descriptions[code]["shortname"] = name
            mydict["categorical"] = {"descriptions": descriptions, "sort_order": sort_order}

        return mydict

    def setIntType(self):
        try:
            alreadyExists = self.intType
        except AttributeError:
            cursor = self.dbToPutIn.query("SELECT count(DISTINCT "+ self.field + ") FROM " + self.table)
            self.nCategories = cursor.fetchall()[0][0]
            self.intType = "INT UNSIGNED"
            if self.nCategories <= 16777215:
                self.intType = "MEDIUMINT UNSIGNED"
            if self.nCategories <= 65535:
                self.intType = "SMALLINT UNSIGNED"
            if self.nCategories <= 255:
                self.intType = "TINYINT UNSIGNED"

    def buildIdTable(self):

        """
        This builds an integer crosswalk ID table with a field that stores categorical
        information in the fewest number of bytes. This is important because it can take
        significant amounts of time to group across categories if they are large: 
        for example, with 4 million newspaper articles, on one server a GROUP BY with 
        a 12-byte VARCHAR field takes 5.5 seconds, but a GROUP BY with a 3-byte MEDIUMINT
        field corresponding exactly to that takes 2.2 seconds on the exact same data.
        That sort of query is included in every single bookworm 
        search multiple times, so it's necessary to optimize. Plus, it means we can save space on memory storage
        in important ways as well.
        """
        #First, figure out how long the ID table has to be and make that into a datatype.
        #Joins and groups are slower the larger the field grouping on, so this is worth optimizing.
        self.setIntType()

        returnt = "DROP TABLE IF EXISTS tmp;\n\n"
        returnt += "CREATE TABLE tmp ENGINE=MEMORY SELECT  %(field)s,count(*) as count FROM  %(table)s GROUP BY  %(field)s;\n\n" % self.__dict__
        returnt += """CREATE TABLE IF NOT EXISTS %(field)s__id (
                      %(field)s__id %(intType)s PRIMARY KEY AUTO_INCREMENT,
                      %(field)s VARCHAR (255), INDEX (%(field)s), %(field)s__count MEDIUMINT);\n\n""" % self.__dict__
        returnt += """INSERT INTO %(field)s__id (%(field)s,%(field)s__count) 
                      SELECT %(field)s,count FROM tmp LEFT JOIN %(field)s__id USING (%(field)s) WHERE %(field)s__id.%(field)s__id IS NULL 
                      ORDER BY count DESC;\n\n""" % self.__dict__
        returnt += """DROP TABLE tmp;\n\n"""

        self.idCode = "%s__id" % self.field
        return returnt


def splitMySQLcode(string):
    """
    MySQL code can only be executed one command at a time, and fails if it has any empty slots
    """
    output = ['%s;\n' % query for query in string.split(';') if re.search(r"\w", query)]
    return output

class variableSet:

    def __init__(self, jsonDefinition, anchorField='bookid'):
        self.variables = [dataField(item) for item in jsonDefinition]
        self.anchorField = anchorField
        """
        Any set of variables could be 'anchored' to any datafield that ultimately
        checks back into 'bookid' (which is the reserved term that we use for the lowest
        level of indexing--it can be a book, a newspaper page, a journal article, whatever).
        If anchor is something other than bookid, there will be a set of relational joins 
        set up to bring it back to bookid in the end.

        THis hasn't been implemented fully yet, but would be extremely useful for every dataset I've looked at.
        """

    def uniques(self):
        return [variable for variable in self.variables if variable.unique]

class textids(dict):
    """
    This class is a dictionary that maps file-locations (which can be many characters long)
    to bookids (which are 3-byte integers).
    It's critically important to keep the already-existing data valid; so it doesn't overwrite the
    old stuff, instead it makes sure this python dictionary is always aligned with the text files on
    disk. As a result, additions to it always have to be made through the 'bump' method rather than
    ordinary assignment (since I, Ben, didn't know how to reset the default hash assignment to include
    this): and it has to be closed at the end to ensure the file is up-to-date at the end.
    """

    #Create a dictionary, and initialize it with all the bookids we already have.
    #And make it so that any new entries are also written to disk, so that they are kept permanently.
    def __init__(self):
        try:
            subprocess.call(['mkdir','files/texts/textids'])
        except:
            pass
        filelists = os.listdir("files/texts/textids")
        numbers = [0]
        for filelist in filelists:
            for line in open("files/texts/textids/%s" % filelist):
                parts = line.replace('\n', '').split("\t")
                self[parts[1]] = int(parts[0])
                numbers.append(int(parts[0]))
        self.new = open('files/texts/textids/new', 'a')
        self.max = max(numbers)
    
    def bump(self,newFileName):
        self.max = self.max + 1
        writing = self.new
        writing.write('%s\t%s\n' % (str(self.max), newFileName.encode('utf-8')))
        self[newFileName] = self.max
        return self.max
    
    def close(self):
        self.new.close()


def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, decimal.Decimal):
        obj = unicode(str(obj), encoding)
    return obj


def write_metadata(variables, limit=float("inf")):
    #Write out all the metadata into files that MySQL is able to read in.
    linenum = 1
    bookids = textids()
    metadatafile = open("files/metadata/jsoncatalog_derived.txt")
    catalog = open("files/metadata/catalog.txt", 'w')
    for variable in [variable for variable in variables if not variable.unique]:
        #Don't open until here, because otherwise it destroys the existing files, I belatedly realized,
        #making stop-and-go debugging harder.
        variable.output = open(variable.outputloc, 'w')
    for entry in metadatafile:
        try:
            entry = to_unicode(entry)
            entry = entry.replace('\\n', ' ')
            entry = json.loads(entry)
        except:
            print "WARNING: json parsing failed for this JSON line:"
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print entry
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            continue
            #raise
        #We always lead with the bookid and the filename. Unicode characters in filenames may cause problems.
        filename = to_unicode(entry['filename'])
        try:
            bookid = bookids[entry['filename']]
        except KeyError:
            bookid = bookids.bump(entry['filename'])
        mainfields = [str(bookid),to_unicode(entry['filename'])]
        #First, pull the unique variables and write them to the 'catalog' table
        for var in [variable for variable in variables if variable.unique]:
            myfield = entry.get(var.field, "")
            mainfields.append(to_unicode(myfield))
        try:
            catalogtext = '%s\n' % '\t'.join(mainfields)
        except:
            print mainfields
            raise
        catalog.write(catalogtext.encode('utf-8'))
        for variable in [variable for variable in variables if not variable.unique]:
             #Each of these has a different file it must write to...
            outfile = variable.output
            lines = entry.get(variable.field, [])
            for line in lines:
                try:
                    writing = '%s\t%s\n' % (str(bookid), line)
                    outfile.write(writing.encode('utf-8'))
                except:
                    print "some sort of error with bookid no. " +str(bookid) + ": " + json.dumps(lines)
                    pass
        if linenum > limit:
           break
        linenum=linenum+1
    for variable in [variable for variable in variables if not variable.unique]:
        variable.output.close()
    bookids.close()
    catalog.close()


class BookwormSQLDatabase:
    """
    This class gives interactions methods to a MySQL database storing Bookworm data.
    Although the primary methods are about loading data already created into the SQL database, it has a few other operations
    that write out text files needed by the API and the web front end: I take it as logical to do those here, since that how
    it fits chronologically in the bookworm-creation sequence.
    """
    def __init__(self,dbname,dbuser,dbpassword):
        self.dbname = dbname
        self.dbuser = dbuser
        self.dbpassword = dbpassword
        try:
            variablefile = open("files/metadata/field_descriptions_derived.json", 'r')
        except:
            raise
        self.db = DB(dbname)
        variables = json.loads(variablefile.read())
        self.variables = [dataField(variable,self.db) for variable in variables]

    def create_database(self):
        dbname = self.dbname
        dbuser = self.dbuser
        dbpassword = self.dbpassword
        db = self.db
        #This must be run as a MySQL user with create_table privileges
        try:
            db.query("CREATE DATABASE " + dbname)
        except:
            print "Database %s already exists: that might be intentional, so not dying" % dbname
        try:
            "Setting up permissions for web user..."
            db.query("GRANT SELECT ON " + dbname + ".*" + " TO '" + dbuser + "'@'%' IDENTIFIED BY '" + dbpassword + "'")
        except:
            print "Something went wrong with the permissions"
            raise
        try:
            #a field to store stuff we might need later.
            db.query("CREATE TABLE IF NOT EXISTS bookworm_information (entry VARCHAR(255), PRIMARY KEY (entry), value VARCHAR(50000))")
        except:
            raise
            
    def load_book_list(self):
        db = self.db
        print "Making a SQL table to hold the catalog data"
        mysqlfields = ["bookid MEDIUMINT, PRIMARY KEY(bookid)", "filename VARCHAR(255)", "nwords INT"]
        for variable in [variable for variable in self.variables if variable.unique]:
            createstring = variable.slowSQL(withIndex=True)
            mysqlfields.append(createstring)
        #This creates the main (slow) catalog table
        db.query("""DROP TABLE IF EXISTS catalog""")
        createcode = """CREATE TABLE IF NOT EXISTS catalog (
            """ + ",\n".join(mysqlfields) + ");"
        try:
            db.query(createcode)
        except:
            print "error executing " + createcode
            raise

        #Never have keys before a LOAD DATA INFILE
        db.query("ALTER TABLE catalog DISABLE KEYS")
        print "loading data into catalog using LOAD DATA LOCAL INFILE..."
        loadcode = """LOAD DATA LOCAL INFILE 'files/metadata/catalog.txt' 
                   INTO TABLE catalog FIELDS ESCAPED BY ''
                   (bookid,filename,""" + ','.join([field.field for field in self.variables if field.unique]) + """) 
                   """
        print loadcode
        db.query(loadcode)
        print "enabling keys on catalog"
        db.query("ALTER TABLE catalog ENABLE KEYS")

        #If there isn't a 'searchstring' field, it may need to be coerced in somewhere hereabouts

        #This here stores the number of words in between catalog updates, so that the full word counts only have to be done once since they're time consuming.
        db.query("CREATE TABLE IF NOT EXISTS nwords (bookid MEDIUMINT, PRIMARY KEY (bookid), nwords INT);")
        db.query("UPDATE catalog JOIN nwords USING (bookid) SET catalog.nwords = nwords.nwords")
        db.query("INSERT INTO nwords (bookid,nwords) SELECT catalog.bookid,sum(count) FROM catalog LEFT JOIN nwords USING (bookid) JOIN master_bookcounts USING (bookid) WHERE nwords.bookid IS NULL GROUP BY catalog.bookid")
        db.query("UPDATE catalog JOIN nwords USING (bookid) SET catalog.nwords = nwords.nwords")

        #And then make the ones that are distinct:
        alones = [variable for variable in self.variables if not variable.unique]

        for dfield in alones:
            print "Making a SQL table to hold the data for " + dfield.field
            db.query("""DROP TABLE IF EXISTS """       + dfield.field + "Disk")
            db.query("""CREATE TABLE IF NOT EXISTS """ + dfield.field + """Disk (
            bookid MEDIUMINT, 
            """ +dfield.slowSQL(withIndex=True) + """
            );""")
            db.query("ALTER TABLE " + dfield.field + "Disk DISABLE KEYS;")
            loadcode = """LOAD DATA LOCAL INFILE 'files/metadata/""" + dfield.field +  """.txt' INTO TABLE """ + dfield.field + """Disk
                   FIELDS ESCAPED BY '';"""
            db.query(loadcode)
            cursor = db.query("""SELECT count(*) FROM """ + dfield.field + """Disk""")
            print "length is\n" + str(cursor.fetchall()[0][0]) + "\n\n\n"
            db.query("ALTER TABLE " + dfield.field + "Disk ENABLE KEYS")
        
        needingLookups = [variable for variable in self.variables if variable.datatype=="categorical"]

        for dfield in needingLookups:
            print "Building a lookup table for " + dfield.field
            #First make the id table
            for query in splitMySQLcode(dfield.buildIdTable()):
                dfield.dbToPutIn.query(query)

    def load_word_list(self):
        db = self.db
        print "Making a SQL table to hold the words"
        db.query("""DROP TABLE IF EXISTS words""")
        db.query("""CREATE TABLE IF NOT EXISTS words (
        wordid MEDIUMINT, 
        word VARCHAR(255), INDEX (word),
        count BIGINT UNSIGNED,
        casesens VARBINARY(255),
        stem VARCHAR(255)
        );""")

        db.query("ALTER TABLE words DISABLE KEYS")
        print "loading data using LOAD DATA LOCAL INFILE"
        db.query("""LOAD DATA LOCAL INFILE 'files/texts/wordlist/wordlist.txt' 
                   INTO TABLE words
                   CHARACTER SET binary
                   (wordid,word,count) """)
        print "creating indexes on words table"
        db.query("ALTER TABLE words ENABLE KEYS")
        db.query("UPDATE words SET casesens=word")

    def create_unigram_book_counts(self):
        db = self.db
        db.query("""DROP TABLE IF EXISTS master_bookcounts""")
        print "Making a SQL table to hold the unigram counts"
        db.query("""CREATE TABLE IF NOT EXISTS master_bookcounts (
        bookid MEDIUMINT UNSIGNED NOT NULL, INDEX(bookid,wordid,count),
        wordid MEDIUMINT UNSIGNED NOT NULL, INDEX(wordid,bookid,count),    
        count MEDIUMINT UNSIGNED NOT NULL);""")
        db.query("ALTER TABLE master_bookcounts DISABLE KEYS")
        print "loading data using LOAD DATA LOCAL INFILE"
        for line in open("files/metadata/catalog.txt"):
            fields = line.split()
            try:
                db.query("LOAD DATA LOCAL INFILE 'files/texts/encoded/unigrams/"+fields[1]+".txt' INTO TABLE master_bookcounts CHARACTER SET utf8 (wordid,count) SET bookid="+fields[0]+";")
            except:
                pass
        print "Creating Unigram Indexes"
        db.query("ALTER TABLE master_bookcounts ENABLE KEYS")

    def create_bigram_book_counts(self):
        db = self.db
        print "Making a SQL table to hold the bigram counts"
        db.query("""DROP TABLE IF EXISTS master_bigrams""")
        db.query("""CREATE TABLE IF NOT EXISTS master_bigrams (
        bookid MEDIUMINT NOT NULL, 
        word1 MEDIUMINT NOT NULL, INDEX (word1,word2,bookid,count),    
        word2 MEDIUMINT NOT NULL,     
        count MEDIUMINT UNSIGNED NOT NULL);""")
        db.query("ALTER TABLE master_bigrams DISABLE KEYS")
        print "loading data using LOAD DATA LOCAL INFILE"
        for line in open("files/metadata/catalog.txt"):
            fields = line.split()
            try:
                db.query("LOAD DATA LOCAL INFILE 'files/texts/encoded/bigrams/"+fields[1]+".txt' INTO TABLE master_bigrams (word1,word2,count) SET bookid="+fields[0]+";")
            except:
                pass
        print "Creating bigram indexes"
        db.query("ALTER TABLE master_bigrams ENABLE KEYS")

    def create_memory_table_script(self,run=True):
        ###This is the part that has to run on every startup. Now we make a SQL code that can just run on its own, stored in the root directory.
        
        commands = ["USE " + self.dbname + ";"]
        commands.append("DROP TABLE IF EXISTS tmp;");


        for variable in [variable for variable in self.variables if variable.datatype=="categorical"]:
            """
            All the categorical variables get a lookup table
            """
            a = variable.fastLookupTableIfNecessary("MEMORY")
            print a
            commands.append(variable.fastLookupTableIfNecessary())
            
        commands.append("""
        CREATE TABLE tmp
        (bookid MEDIUMINT, PRIMARY KEY (bookid),
        nwords MEDIUMINT,""" +",\n".join([variable.fastSQL() for variable in self.variables if (variable.unique and variable.fastSQL() is not None)]) + """
        )
        ENGINE=MEMORY;""");

        commands.append("INSERT INTO tmp SELECT bookid,nwords, " + ",".join([variable.fastField for variable in self.variables if variable.unique and variable.fastSQL() is not None]) + " FROM catalog " + " ".join([" JOIN %(field)s__id USING (%(field)s ) " % variable.__dict__ for variable in self.variables if variable.unique and variable.fastSQL() is not None and variable.datatype=="categorical"])+ ";");

        commands.append("DROP TABLE IF EXISTS fastcat;");
        commands.append("RENAME TABLE tmp TO fastcat;");
        commands.append("CREATE TABLE tmp (wordid MEDIUMINT, PRIMARY KEY (wordid), word VARCHAR(30), INDEX (word), casesens VARBINARY(30),UNIQUE INDEX(casesens), lowercase CHAR(30), INDEX (lowercase) ) ENGINE=MEMORY;")
        #For some reason, there are some duplicate keys; INSERT IGNORE skips those. It might be worth figuring out exactly how they creep in: it looks to me like it has to with unicode or other non-ascii characters,
        #so we may be losing a few of those here.
        commands.append("INSERT IGNORE INTO tmp SELECT wordid as wordid,word,casesens,LOWER(word) FROM words WHERE CHAR_LENGTH(word) <= 30 AND wordid <= 1500000 ORDER BY wordid;")
        commands.append("DROP TABLE IF EXISTS wordsheap;");
        commands.append("RENAME TABLE tmp TO wordsheap;");

        for variable in [variable for variable in self.variables if not variable.unique]:
            commands.append(variable.fastSQLTable("MEMORY"))

        SQLcreateCode = open('files/createTables.SQL', 'w')
        for line in commands:
        #Write them out so they can be put somewhere to run automatically on startup:
            try:
                SQLcreateCode.write('%s\n' % line)
            except:
                print line
                raise
        if run:
            for line in commands:
                for query in splitMySQLcode(line):
                    self.db.query(query)
        return commands

    def jsonify_data(self):
        variables = self.variables
        dbname = self.dbname
        #This creates a JSON file compliant with the Bookworm web site.
        output = dict()
        output['settings'] = {
                              "dbname": self.dbname,
                              "itemName":" text",
                              "sourceName": self.dbname,
                              "sourceURL": self.dbname
                             }
        ui_components = [
                         {
                          "type":"text",
                          "dbfield":"word",
                          "name":"Word(s)"
                         }
                        ]
        for variable in variables:
            newdict = variable.jsonDict()
            if newdict: #(It can be empty, in which case we don't want it for the json)
                ui_components.append(newdict)
        try:
            mytime = [variable.field for variable in variables if variable.datatype=='time'][0]
            output['default_search']  = [
                                         {
                                          "search_limits": [{"word":["test"]}],
                                          "time_measure": mytime,
                                          "words_collation": "Case_Sensitive",
                                          "counttype": "Occurrences_per_Million_Words",
                                          "smoothingSpan": 0
                                         }
                                        ]
        except:
            print "Not enough info for a default search"
            raise
        output['ui_components'] = ui_components
        outfile = open('files/%s.json' % dbname, 'w')
        outfile.write(json.dumps(output))

    def create_API_settings(self):
        db = self.db
        try:
            db.query("DROP TABLE IF EXISTS API_settings")
            db.query("CREATE TABLE API_settings (settings VARCHAR(8192));")
        except:
            pass
        api_info = {
                    "HOST": "10.102.15.45",
                    "database": self.dbname,
                    "fastcat": "fastcat",
                    "fullcat": "catalog",
                    "fastword": "wordsheap",
                    "read_default_file": "/etc/mysql/my.cnf",
                    "fullword": "words",
                    "separateDataTables": [variable.field for variable in self.variables if not (variable.unique or variable.type=="etc") ],
                    "read_url_head": "arxiv.culturomics.org"
                   }
        addCode = json.dumps(api_info)
        print addCode
        db.query("INSERT INTO API_settings VALUES ('%s');" % addCode)

    def update_Porter_stemming(self): #We use stems occasionally.
        print "Updating stems from Porter algorithm..."
        from nltk import PorterStemmer
        stemmer = PorterStemmer()
        cursor = db.query("""SELECT word FROM words""")
        words = cursor.fetchall()
        for local in words:
            word = ''.join(local) #Could probably take the first element of the tuple as well?
            #Apostrophes have the save stem as the word, if they're included        
            word = word.replace("'s","")
            if re.match("^[A-Za-z]+$",word):
                query = """UPDATE words SET stem='""" + stemmer.stem(''.join(local)) + """' WHERE word='""" + ''.join(local) + """';"""
                z = cursor.execute(query)
