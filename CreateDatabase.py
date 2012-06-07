#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import MySQLdb
import re
import sys
import json
import os
txtdir = "../"

#First off: what are we using? Pull a dbname from command line input.
#As well as the username and password.
try:
    dbname = sys.argv[1]
    #The dbuser and db password aren't too secure--they should be read-only in any case--but no point exposing them anyway, even though it makes this a bit trickier to run.
    dbuser = sys.argv[2]
    dbpassword = sys.argv[3]
    try:
        variablefile = open("metadataParsers/" + dbname + "/" + dbname + ".json",'r')
    except:
        sys.exit("you must have a json file for your database located in metadataParsers: see the README in presidio/metadata")
    variables = json.loads(''.join(variablefile.readlines()))
except:
    raise

#Then define a class that supports a data field from a json definition.
#We'll use this to spit out appropriate sql code and JSON objects where needed.
class dataField():
    def __init__(self,definition):
        for key in definition.keys():
            vars(self)[key] = definition[key]
        #The table it's stored in will be either catalog, or it's own name
        if self.unique:
            self.table = "catalog"
            self.fasttab = "fastcat"
        else:
            self.table = self.field + "Disk"
            self.fasttab = self.field
            self.output = open("../metadata/" + variable['field'] + ".txt",'w')

    def slowSQL(self):
        #This returns something like """author VARCHAR(255)"""
        mysqltypes = {"character":"VARCHAR(255)","integer":"INT","text":"VARCHAR(5000)"}
        createstring = " " + self.field + " " + mysqltypes[self.type]
        return createstring

    def fastSQL(self):
        #This creates code to go in a memory table: it assumes that the disk tables are already there, and that a connection cursor is active.
        #Memory tables DON'T SUPPORT VARCHAR; thus, it has to be stored this other way.
        if self.type == "character":
            cursor.execute("SELECT max(char_length("+self.field+")) FROM " + self.table)
            length = cursor.fetchall()[0][0]
            return " " + self.field + " " + "VARCHAR(" + str(int(length)) + ")"
        if self.type == "integer":
            return " " + self.field + " " + "INT"
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
            cursor.execute("SELECT MIN(" + self.field + "), MAX(" + self.field + ") FROM catalog")
            results = cursor.fetchall()[0]
            mydict['range'] = [results[0],results[1]]
            mydict['initial'] = [results[0],results[1]]
        if (self.datatype=="categorical"):
            #Find all the variables used more than 100 times from the database, and build them into something json-usable.
            cursor.execute("SELECT " + self.field + ",count(*) as count from " + self.fasttab + " GROUP BY " + self.field + " HAVING count >= 250 ORDER BY count DESC")
            sort_order = []
            descriptions = dict()
            for row in cursor.fetchall():
                code = row[0]
                sort_order.append(code)
                descriptions[code] = dict()
                #These three things all have slightly different meanings: the english name, the database code for that name, and the short display name to show. It would be worth allowing lookup files for these: for now, they are what they are and can be further improved by hand.
                descriptions[code]["dbcode"] = code
                descriptions[code]["name"] = code
                descriptions[code]["shortname"] = code
            mydict["categorical"] = {"descriptions":descriptions,"sort_order":sort_order}
        return mydict

uniqueVariables = []
arrayVariables = []
uniqueVariableNames = []
arrayVariableNames = []
allVariables = [dataField(variable) for variable in variables]

dataFields = dict()
catalog = open("../metadata/catalog.txt",'w')
#Metadatafile is a file of json rows with keys for metadata.
metadatafile = open("../metadata/jsoncatalog.txt")

class textids(dict):
    #Create a dictionary, and initialize it with all the bookids we already have.
    #And make it so that any new entries are also written to disk, so that they are kept permanently.
    def __init__(self):
        try:
            subprocess.call(['mkdir','../texts/textids'])
        except:
            raise
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
        writing.write(str(self.max) + "\t" + newFileName + "\n")
        self[newFileName] = self.max
        return self.max
    def close(self):
        self.new.close()

for variable in variables:
    dataFields[variable['field']] = dataField(variable)
    if variable.get("unique",True):
        uniqueVariables.append(dataField(variable))
        uniqueVariableNames.append(variable['field'])
    else:
        uniqueVariables.append(dataField(variable))
        arrayVariableNames.append(variable['field'])
        #This will create as many separate files as there are categorical data.


#This function turns out to be pretty helpful.
def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def write_metadata(limit = float("inf")):
    linenum = 1
    bookids = textids()
    metadatafile = open("../metadata/jsoncatalog.txt")
    for entry in metadatafile:
        try:
            entry = to_unicode(entry)
            entry = json.loads(entry)
        except:
            raise
        #We always lead with the bookid and the filename. Unicode characters in filenames may cause problems.
        filename = to_unicode(entry['filename'])
        try:
            bookid = bookids[entry['filename']]
        except KeyError:
            bookid = bookids.bump(entry['filename'])
        mainfields = [str(bookid),to_unicode(entry['filename'])]
        #First, pull the unique variables and write them to the 'catalog' table
        for var in uniqueVariableNames:
            myfield = entry.get(var,"")
            mainfields.append(to_unicode(myfield))
            #Adding str() to the line below--hopefully it won't mess up the unicoding.
        catalogtext = '\t'.join(str(mainfields)) + "\n"
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


variables = [dataField(variable) for variable in variables]
#This must be run as a MySQL user with create_table privileges
cnx = MySQLdb.connect(read_default_file="~/.my.cnf",use_unicode = 'True',charset='utf8',db = dbname)
cursor = cnx.cursor()
cursor.execute("SET NAMES 'utf8'")
cursor.execute("SET CHARACTER SET 'utf8'")
cursor.execute("USE " + dbname)

def create_database():
    try:
        cursor.execute("CREATE DATABASE " + dbname)
    except:
        print "Database " + dbname + " already exists: that might be intentional, so not dying"
    try:
        "Setting up permissions for web user..."
        cursor.execute("GRANT SELECT ON " + dbname + ".*" + " TO '" + dbuser + "'@'%' IDENTIFIED BY '" + dbpassword + "'")
    except:
        print "Something went wrong with the permissions"
        raise

def load_book_list():
    catalog.close()
    print "Making a SQL table to hold the catalog data"
    mysqlfields = ["bookid MEDIUMINT, PRIMARY KEY(bookid)","filename VARCHAR(255)","nwords INT"]
    for variable in [variable for variable in variables if variable.unique]:
        createstring = variable.slowSQL()
        mysqlfields.append(createstring)
    #This creates the main (slow) catalog table
    cursor.execute("""DROP TABLE IF EXISTS catalog""")
    createcode = """CREATE TABLE IF NOT EXISTS catalog (
        """ + ",\n".join(mysqlfields) + """
        );"""
    cursor.execute(createcode)
    #Never have keys before a LOAD DATA INFILE
    cursor.execute("ALTER TABLE catalog DISABLE KEYS")
    print "loading data into catalog using LOAD DATA LOCAL INFILE..."
    loadcode = """LOAD DATA LOCAL INFILE '../metadata/catalog.txt' 
                   INTO TABLE catalog
                   (bookid,filename,""" + ','.join([field.field for field in variables if field.unique]) + """) """
    print loadcode
    cursor.execute(loadcode)
    cursor.execute("ALTER TABLE catalog ENABLE KEYS")
    #If there isn't a 'searchstring' field, it may need to be coerced in somewhere hereabouts
    cursor.execute("UPDATE catalog SET nwords = (SELECT sum(count) FROM master_bookcounts WHERE master_bookcounts.bookid = catalog.bookid) WHERE nwords is null;")
    #And then make the ones that are distinct:
    alones = [variable for variable in variables if not variable.unique]
    for dfield in alones:
        dfield.output.close()
        print "Making a SQL table to hold the data for " + dfield.field
        cursor.execute("""DROP TABLE IF EXISTS """       + dfield.field + "Disk")
        cursor.execute("""CREATE TABLE IF NOT EXISTS """ + dfield.field + """Disk (
            bookid MEDIUMINT, 
            """ +dfield.slowSQL() + """, PRIMARY KEY (bookid,""" +dfield.field + """)
            );""")
        cursor.execute("ALTER TABLE " + dfield.field + "Disk DISABLE KEYS;")
        loadcode = """LOAD DATA LOCAL INFILE '../metadata/""" + dfield.field +  """.txt' INTO TABLE """ + dfield.field + """Disk;"""
        cursor.execute(loadcode)
        cursor.execute("""SELECT count(*) FROM disciplineDisk""")
        print "length is\n" + str(cursor.fetchall()[0][0]) + "\n\n\n"
        cursor.execute("ALTER TABLE " + dfield.field + "Disk ENABLE KEYS")

def load_word_list():
    print "Making a SQL table to hold the words"
    cursor.execute("""CREATE TABLE IF NOT EXISTS words (
        wordid MEDIUMINT, 
        word VARCHAR(255), INDEX (word),
        count BIGINT UNSIGNED,
        casesens VARBINARY(255),
        stem VARCHAR(255)
        );""")
    cursor.execute("ALTER TABLE words DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '../texts/wordlist/wordlist.txt' 
                   INTO TABLE words
                   CHARACTER SET binary
                   (wordid,word,count) """)
    cursor.execute("ALTER TABLE words ENABLE KEYS")
    cursor.execute("UPDATE words SET casesens=word")

def create_unigram_book_counts():
    print "Making a SQL table to hold the unigram counts"
    cursor.execute("""CREATE TABLE IF NOT EXISTS master_bookcounts (
        bookid MEDIUMINT NOT NULL, INDEX(bookid,wordid,count),
        wordid MEDIUMINT NOT NULL, INDEX(wordid,bookid,count),    
        count MEDIUMINT UNSIGNED NOT NULL);""")
    cursor.execute("ALTER TABLE master_bookcounts DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    for line in open(txtdir+"metadata/catalog.txt"):
        fields = line.split()
        try:
            cursor.execute("LOAD DATA LOCAL INFILE '../texts/encoded/unigrams/"+fields[1]+".txt' INTO TABLE master_bookcounts CHARACTER SET utf8 (wordid,count) SET bookid="+fields[0]);
        except:
            pass
    cursor.execute("ALTER TABLE master_bookcounts ENABLE KEYS")

def create_bigram_book_counts():
    print "Making a SQL table to hold the bigram counts"
    cursor.execute("""CREATE TABLE IF NOT EXISTS master_bigrams (
        bookid MEDIUMINT NOT NULL, 
        word1 MEDIUMINT NOT NULL, INDEX (word1,word2,bookid,count),    
        word2 MEDIUMINT NOT NULL,     
        count MEDIUMINT UNSIGNED NOT NULL);""")
    cursor.execute("ALTER TABLE master_bigrams DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    for line in open(txtdir+"metadata/catalog.txt"):
        fields = line.split()
        try:
            cursor.execute("LOAD DATA LOCAL INFILE '../texts/encoded/bigrams/"+fields[1]+".txt' INTO TABLE master_bigrams (word1,word2,count) SET bookid="+fields[0]);
        except:
            pass
    cursor.execute("ALTER TABLE master_bigrams ENABLE KEYS")

###This is the part that has to run on every startup. Now we make a SQL code that can just run on its own, stored in the root directory.
def create_memory_table_script(variables,run=True):
    commands = ["USE " + dbname + ";"]
    commands.append("DROP TABLE IF EXISTS tmp;");
    commands.append("""CREATE TABLE tmp
     (bookid MEDIUMINT, PRIMARY KEY (bookid),
      nwords MEDIUMINT,""" +",\n".join([variable.fastSQL() for variable in variables if (variable.unique and variable.fastSQL() is not None)]) + """
      )
    ENGINE=MEMORY;""");
    commands.append("INSERT INTO tmp SELECT bookid,nwords, " + ",".join([variable.field for variable in variables if variable.unique and variable.fastSQL() is not None]) + " FROM catalog;");
    commands.append("DROP TABLE IF EXISTS fastcat;");
    commands.append("RENAME TABLE tmp TO fastcat;");
    commands.append("CREATE TABLE tmp (wordid MEDIUMINT, PRIMARY KEY (wordid), word VARCHAR(30), INDEX (word), casesens VARBINARY(30),UNIQUE INDEX(casesens), lowercase CHAR(30), INDEX (lowercase) ) ENGINE=MEMORY;")
    #For some reason, there are some duplicate keys; INSERT IGNORE skips those. It might be worth figuring out exactly how they creep in: it looks to me like it has to with unicode or other non-ascii characters,
    #so we may be losing a few of those here.
    commands.append("INSERT IGNORE INTO tmp SELECT wordid as wordid,word,casesens,LOWER(word) FROM words WHERE CHAR_LENGTH(word) <= 30 AND wordid <= 1500000 ORDER BY wordid;")
    commands.append("DROP TABLE IF EXISTS wordsheap;");
    commands.append("RENAME TABLE tmp TO wordsheap;");
    for variable in [variable for variable in variables if not variable.unique]:
        commands.append("CREATE TABLE tmp (bookid MEDIUMINT, " + variable.fastSQL() + ", PRIMARY KEY (bookid," + variable.field + ")) ENGINE=MEMORY ;");
        commands.append("INSERT into tmp SELECT * FROM " +  variable.field +  "Disk  ")
        commands.append("DROP TABLE IF EXISTS " +  variable.field)
        commands.append("RENAME TABLE tmp TO " + variable.field)
    SQLcreateCode = open("../createTables.SQL",'w')
    for line in commands:
        #Write them out so they can be put somewhere to run automatically on startup:
        SQLcreateCode.write(line + "\n")
    if run:
        for line in commands:
            #Run them, too.
            cursor.execute(line)

def jsonify_data(variables):
    #This creates a JSON file compliant with the Bookworm web site.
    output = dict()
    output['settings'] = {"dbname":dbname,"itemName":"text","sourceName":dbname,"sourceURL":dbname}
    ui_components = [{"type":"text","dbfield":"word","name":"Word(s)"}]
    for variable in variables:
        newdict = variable.jsonDict()
        if newdict: #(It can be empty, in which case we don't want it for the json)
            ui_components.append(newdict)
    try:
        mytime = [variable.field for variable in variables if variable.datatype=='time'][0]
        output['default_search']  = [{"search_limits":[{"word":["test"]}],"time_measure":mytime,"words_collation":"Case_Sensitive","counttype":"Occurrences_per_Million_Words","smoothingSpan":5}]
    except:
        print "Not enough info for a default search"
        raise
    output['ui_components'] = ui_components
    outfile = open("../" + dbname + ".json",'w')
    outfile.write(json.dumps(output))

def create_API_settings(variables):
    try:
        cursor.execute("DROP TABLE IF EXISTS API_settings")
        cursor.execute("CREATE TABLE API_settings (settings VARCHAR(8192));")
    except:
        pass
    addCode = json.dumps({"HOST":"10.102.15.45","database":dbname,"fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","read_default_file":"/etc/mysql/my.cnf","fullword":"words","separateDataTables":[variable.field for variable in variables if not (variable.unique or variable.type=="etc") ],"read_url_head":"arxiv.culturomics.org" })
    print addCode
    cursor.execute("INSERT INTO API_settings VALUES ('" + addCode + "');")

