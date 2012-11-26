#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import MySQLdb
import re
import sys
import json
import os
import decimal


#First off: what are we using? Pull a dbname from command line input.
#As well as the username and password.
	
class DB:
    def __init__(self, dbname):
        self.dbname = dbname
        self.conn = None

    def connect(self):
        #These scripts run as the Bookworm _Administrator_ on this machine.
        self.conn = MySQLdb.connect(read_default_file="~/.my.cnf",use_unicode = 'True',charset='utf8',db = '')
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS "+self.dbname)
        #Don't use native query attribute here to avoid infinite loops
        cursor.execute("SET NAMES 'utf8'")
        cursor.execute("SET CHARACTER SET 'utf8'")
        cursor.execute("SET storage_engine=MYISAM")
        cursor.execute("USE " + self.dbname)

    def query(self, sql):
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
    Looking at this again, I think it might actually lose all the dict attributes. But that's OK.
    """
    def __init__(self,definition,dbToPutIn):
        for key in definition.keys():
            vars(self)[key] = definition[key]
        self.dbToPutIn = dbToPutIn
        #The table it's stored in will be either catalog, or it's own name
        if self.unique:
            self.table = "catalog"
            self.fasttab = "fastcat"
        else:
            self.table = self.field + "Disk"
            self.fasttab = self.field
            self.output = open("../metadata/" + self.field + ".txt",'w')

    def slowSQL(self,withIndex=False):
        #This returns something like """author VARCHAR(255)"""
        mysqltypes = {"character":"VARCHAR(255)","integer":"INT","text":"VARCHAR(5000)","decimal":"DECIMAL (9,4)"}
        indexstring = ", INDEX (bookid," + self.field 
        #need to specify fixed prefix length on text strings: (http://dev.mysql.com/doc/refman/5.0/en/create-index.html)
        indextypes = {"character":indexstring + ")","integer":indexstring + ")","text":indexstring + " (255) )","decimal":indexstring + ")"} 
        createstring = " " + self.field + " " + mysqltypes[self.type]
        if withIndex:
            print createstring + indextypes[self.type]
            return createstring +  indextypes[self.type]
        return createstring

    def fastSQL(self):
        #This creates code to go in a memory table: it assumes that the disk tables are already there, and that a connection cursor is active.
        #Memory tables DON'T SUPPORT VARCHAR; thus, it has to be stored this other way
        if self.datatype!='etc':
            if self.type == "character":
                cursor = self.dbToPutIn.query("SELECT max(char_length("+self.field+")) FROM " + self.table)
                length = max([1,cursor.fetchall()[0][0]]) #in case it's null
                length = min([25,length]) #Cut it off to keep memory requirements reasonable
                return " " + self.field + " " + "VARCHAR(" + str(int(length)) + ")"
            if self.type == "integer":
                return " " + self.field + " " + "INT"
            if self.type == "decimal":
                return " " + self.field + " " + "DECIMAL (9,4) "
            else:
                return None
        else:
            return None

    def jsonDict(self):
        #This builds a JSON dictionary that can be loaded into outside bookworm in the "options.json" file.
        mydict = dict()
        #It gets confusingly named: "type" is the key for real name ("time", "categorical" in the json), but also the mysql key ('character','integer') here. That would require renaming code in a couple places.
        mydict['type'] = self.datatype
        mydict['dbfield'] = self.field
        try:
            mydict['name'] = self.name
        except:
            mydict['name'] = self.field
        if (self.datatype=="etc" or self.type=="text"):
            return dict() #(Some things don't go into the fast settings because they'd take too long)
        if (self.datatype=="time"):
            mydict['unit'] = self.field
            #default to the full min and max date ranges
            #times may not be zero or negative
            cursor = self.dbToPutIn.query("SELECT MIN(" + self.field + "), MAX(" + self.field + ") FROM catalog WHERE " + self.field + " > 0 ")
            results = cursor.fetchall()[0]
            mydict['range'] = [results[0],results[1]]
            mydict['initial'] = [results[0],results[1]]
    
        if (self.datatype=="categorical"):
            #Find all the variables used more than 100 times from the database, and build them into something json-usable.
            myquery="SELECT " + self.field + ",count(*) as count from " + self.table + " GROUP BY " + self.field + " HAVING count >= 250 ORDER BY count DESC"
            cursor = self.dbToPutIn.query(myquery)
            sort_order = []
            descriptions = dict()
            for row in cursor.fetchall():
                code = row[0]
                code = to_unicode(code)
                sort_order.append(code)
                descriptions[code] = dict()
                """
                These three things all have slightly different meanings:
                the english name, the database code for that name, and the short display name to show.
                It would be worth allowing lookup files for these: for now, they are what they are and can be further improved by hand.
                """
                descriptions[code]["dbcode"] = code
                descriptions[code]["name"] = code
                descriptions[code]["shortname"] = code
            mydict["categorical"] = {"descriptions":descriptions,"sort_order":sort_order}

        return mydict



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
            subprocess.call(['mkdir','../texts/textids'])
        except:
            pass
        filelists = os.listdir("../texts/textids")
        numbers = [0]
        for filelist in filelists:
            reading = open("../texts/textids/" + filelist)
            for line in reading:
                line = re.sub("\n","",line)
                parts = line.split("\t")
                self[parts[1]] = int(parts[0])
                numbers.append(int(parts[0]))
        self.new = open("../texts/textids/new",'a')
        self.max = max(numbers)
    def bump(self,newFileName):
        self.max = self.max+1
        writing = self.new
        writing.write(str(self.max) + "\t" + newFileName.encode('utf-8') + "\n")
        self[newFileName] = self.max
        return self.max
    def close(self):
        self.new.close()

def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    if isinstance(obj,int) or isinstance(obj,float) or isinstance(obj,decimal.Decimal):
        obj=unicode(str(obj),encoding)
    return obj


def write_metadata(variables,limit = float("inf")):
    #Write out all the metadata into files that MySQL is able to read in.
    linenum = 1
    bookids = textids()
    metadatafile = open("../metadata/jsoncatalog_derived.txt")
    catalog = open("../metadata/catalog.txt",'w')
    for entry in metadatafile:
        try:
            entry = to_unicode(entry)
            entry = re.sub("\\n"," ",entry)
            entry = json.loads(entry)
        except:
            print entry
            raise
        #We always lead with the bookid and the filename. Unicode characters in filenames may cause problems.
        filename = to_unicode(entry['filename'])
        try:
            bookid = bookids[entry['filename']]
        except KeyError:
            bookid = bookids.bump(entry['filename'])
        mainfields = [str(bookid),to_unicode(entry['filename'])]
        #First, pull the unique variables and write them to the 'catalog' table
        for var in [variable for variable in variables if variable.unique]:
            myfield = entry.get(var.field,"")
            mainfields.append(to_unicode(myfield))
        try:
            catalogtext = '\t'.join(mainfields) + "\n"
        except:
            print mainfields
            raise
        catalog.write(catalogtext.encode('utf-8'))
        for variable in [variable for variable in variables if not variable.unique]:
             #Each of these has a different file it must write to...
            outfile = variable.output
            lines = entry.get(variable.field,[])
            for line in lines:
                writing = str(bookid)+"\t"+line+"\n"
                outfile.write(writing.encode('utf-8'))
        if linenum > limit:
           break
        linenum=linenum+1
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
            #This is the not-best place to put this.
            variablefile = open("metadataParsers/" + dbname + "/" + dbname + ".json",'r')
        except:
            sys.exit("you must have a json file for your database located in metadataParsers: see the README in presidio/metadata")
                
        self.db = DB(dbname)
        variables = json.loads(variablefile.read())
        self.variables = [dataField(variable,self.db) for variable in variables]

    def create_database(self):
        dbname=self.dbname
        dbuser=self.dbuser
        dbpassword=self.dbpassword
        db=self.db
        #This must be run as a MySQL user with create_table privileges
        try:
            db.query("CREATE DATABASE " + dbname)
        except:
            print "Database " + dbname + " already exists: that might be intentional, so not dying"
        try:
            "Setting up permissions for web user..."
            db.query("GRANT SELECT ON " + dbname + ".*" + " TO '" + dbuser + "'@'%' IDENTIFIED BY '" + dbpassword + "'")
        except:
            print "Something went wrong with the permissions"
            raise

    def load_book_list(self):
        db=self.db
        print "Making a SQL table to hold the catalog data"
        mysqlfields = ["bookid MEDIUMINT, PRIMARY KEY(bookid)","filename VARCHAR(255)","nwords INT"]
        for variable in [variable for variable in self.variables if variable.unique]:
            createstring = variable.slowSQL()
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
        loadcode = """LOAD DATA LOCAL INFILE '../metadata/catalog.txt' 
                   INTO TABLE catalog
                   (bookid,filename,""" + ','.join([field.field for field in self.variables if field.unique]) + """) """
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
            dfield.output.close()
            print "Making a SQL table to hold the data for " + dfield.field
            db.query("""DROP TABLE IF EXISTS """       + dfield.field + "Disk")
            db.query("""CREATE TABLE IF NOT EXISTS """ + dfield.field + """Disk (
            bookid MEDIUMINT, 
            """ +dfield.slowSQL(withIndex=True) + """
            );""")
            db.query("ALTER TABLE " + dfield.field + "Disk DISABLE KEYS;")
            loadcode = """LOAD DATA LOCAL INFILE '../metadata/""" + dfield.field +  """.txt' INTO TABLE """ + dfield.field + """Disk;"""
            db.query(loadcode)
            cursor = db.query("""SELECT count(*) FROM """ + dfield.field + """Disk""")
            print "length is\n" + str(cursor.fetchall()[0][0]) + "\n\n\n"
            db.query("ALTER TABLE " + dfield.field + "Disk ENABLE KEYS")

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
        db.query("""LOAD DATA LOCAL INFILE '../texts/wordlist/wordlist.txt' 
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
        for line in open("../metadata/catalog.txt"):
            fields = line.split()
            try:
                db.query("LOAD DATA LOCAL INFILE '../texts/encoded/unigrams/"+fields[1]+".txt' INTO TABLE master_bookcounts CHARACTER SET utf8 (wordid,count) SET bookid="+fields[0]+";")
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
        for line in open("../metadata/catalog.txt"):
            fields = line.split()
            try:
                db.query("LOAD DATA LOCAL INFILE '../texts/encoded/bigrams/"+fields[1]+".txt' INTO TABLE master_bigrams (word1,word2,count) SET bookid="+fields[0]+";")
            except:
                pass
        print "Creating bigram indexes"
        db.query("ALTER TABLE master_bigrams ENABLE KEYS")

    def create_memory_table_script(self,run=True):
        ###This is the part that has to run on every startup. Now we make a SQL code that can just run on its own, stored in the root directory.
        
        commands = ["USE " + self.dbname + ";"]
        commands.append("DROP TABLE IF EXISTS tmp;");
        commands.append("""CREATE TABLE tmp
     (bookid MEDIUMINT, PRIMARY KEY (bookid),
      nwords MEDIUMINT,""" +",\n".join([variable.fastSQL() for variable in self.variables if (variable.unique and variable.fastSQL() is not None)]) + """
      )
    ENGINE=MEMORY;""");
        commands.append("INSERT INTO tmp SELECT bookid,nwords, " + ",".join([variable.field for variable in self.variables if variable.unique and variable.fastSQL() is not None]) + " FROM catalog;");
        commands.append("DROP TABLE IF EXISTS fastcat;");
        commands.append("RENAME TABLE tmp TO fastcat;");
        commands.append("CREATE TABLE tmp (wordid MEDIUMINT, PRIMARY KEY (wordid), word VARCHAR(30), INDEX (word), casesens VARBINARY(30),UNIQUE INDEX(casesens), lowercase CHAR(30), INDEX (lowercase) ) ENGINE=MEMORY;")
        #For some reason, there are some duplicate keys; INSERT IGNORE skips those. It might be worth figuring out exactly how they creep in: it looks to me like it has to with unicode or other non-ascii characters,
        #so we may be losing a few of those here.
        commands.append("INSERT IGNORE INTO tmp SELECT wordid as wordid,word,casesens,LOWER(word) FROM words WHERE CHAR_LENGTH(word) <= 30 AND wordid <= 1500000 ORDER BY wordid;")
        commands.append("DROP TABLE IF EXISTS wordsheap;");
        commands.append("RENAME TABLE tmp TO wordsheap;");

        for variable in [variable for variable in self.variables if not variable.unique]:
            fast = variable.fastSQL()
            if fast: #It might return none for some reason, in which case, we don't want any of this to happen.
                commands.append("CREATE TABLE tmp (bookid MEDIUMINT, " + variable.fastSQL() + ", INDEX (bookid) ) ENGINE=MEMORY ;");
                commands.append("INSERT into tmp SELECT * FROM " +  variable.field +  "Disk  " + ";")
                commands.append("DROP TABLE IF EXISTS " +  variable.field + ";")
                commands.append("RENAME TABLE tmp TO " + variable.field + ";")

        SQLcreateCode = open("../createTables.SQL",'w')
        for line in commands:
        #Write them out so they can be put somewhere to run automatically on startup:
            SQLcreateCode.write(line + "\n")
        if run:
            for line in commands:
                #Run them, too.
                self.db.query(line)

    def jsonify_data(self):
        variables = self.variables
        dbname = self.dbname
        #This creates a JSON file compliant with the Bookworm web site.
        output = dict()
        output['settings'] = {"dbname":self.dbname,"itemName":"text","sourceName":self.dbname,"sourceURL":self.dbname}
        ui_components = [{"type":"text","dbfield":"word","name":"Word(s)"}]
        for variable in variables:
            newdict = variable.jsonDict()
            if newdict: #(It can be empty, in which case we don't want it for the json)
                ui_components.append(newdict)
        try:
            mytime = [variable.field for variable in variables if variable.datatype=='time'][0]
            output['default_search']  = [{"search_limits":[{"word":["test"]}],"time_measure":mytime,"words_collation":"Case_Sensitive","counttype":"Occurrences_per_Million_Words","smoothingSpan":0}]
        except:
            print "Not enough info for a default search"
            raise
        output['ui_components'] = ui_components
        outfile = open("../" + dbname + ".json",'w')
        outfile.write(json.dumps(output))

    def create_API_settings(self):
        db = self.db
        try:
            db.query("DROP TABLE IF EXISTS API_settings")
            db.query("CREATE TABLE API_settings (settings VARCHAR(8192));")
        except:
            pass
        addCode = json.dumps({"HOST":"10.102.15.45","database":self.dbname,"fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","read_default_file":"/etc/mysql/my.cnf","fullword":"words","separateDataTables":[variable.field for variable in self.variables if not (variable.unique or variable.type=="etc") ],"read_url_head":"arxiv.culturomics.org" })
        print addCode
        db.query("INSERT INTO API_settings VALUES ('" + addCode + "');")

    def update_Porter_stemming(self): #We use stems occasionally.
        print "Updating stems from Porter algorithm..."
        from nltk import PorterStemmer
        stemmer = PorterStemmer()
        cursor = db.query("""SELECT word FROM words""")
        words = cursor.fetchall()
        for local in words:
            word = ''.join(local) #Could probably take the first element of the tuple as well?
            #Apostrophes have the save stem as the word, if they're included        
            word = re.sub("'s","",word)
            if re.match("^[A-Za-z]+$",word):
                query = """UPDATE words SET stem='""" + stemmer.stem(''.join(local)) + """' WHERE word='""" + ''.join(local) + """';"""
                z = cursor.execute(query)




