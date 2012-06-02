#!/usr/bin/python
# -*- coding: utf-8 -*-

# Be sure that txtdir, catfile, and metafile are set correctly

import MySQLdb
import re
import sys
import json

txtdir = "../"

#First off: what are we using? Pull a dbname from command line input.
#I'm just doing the passwords here too, because: where else?
try:
    dbname = sys.argv[1]
    #The dbuser and db password aren't too secure--they should be read-only in any case--but no point exposing them anyway, even though it makes this a bit trickier to run.
    dbuser = sys.argv[2]
    dbpassword = sys.argv[3]
    variablefile = open("metadataParsers/"+dbname+".json",'r')
    variables = json.loads(''.join(variablefile.readlines()))
except:
    raise

class dataField():
    def __init__(self,definition):
        for key in definition.keys():
            vars(self)[key] = definition[key]
    def slowSQL(self):
        #This returns something like """author VARCHAR(255)"""
        mysqltypes = {"character":"VARCHAR(255)","integer":"INT","text":"VARCHAR(5000)"}
        createstring = " " + self.field + " " + mysqltypes[self.type]
        return createstring

uniqueVariables = []
arrayVariables = []
uniqueVariableNames = []
arrayVariableNames = []
dataFields = dict()
catalog = open("../metadata/catalog.txt",'w')
#Metadatafile is a file of json rows with keys for metadata.
metadatafile = open("../metadata/jsoncatalog.txt")

for variable in variables:
    dataFields[variable['field']] = dataField(variable)
    if variable.get("unique",True):
        uniqueVariables.append(dataField(variable))
        uniqueVariableNames.append(variable['field'])
    else:
        uniqueVariables.append(dataField(variable))
        arrayVariableNames.append(variable['field'])
        #This will create as many separate files as there are categorical data.
        arrayVariables[variable['field']]['output'] = open("../metadata/" + variable['field'] + ".txt")

#The bookids are sequentially assigned here.
#It would be better to default to another list first to allow supplemental adds (currently you can only build the whole big database once).
bookid = 1

#And this function turns out to be pretty helpful.
def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

for entry in metadatafile:
    try:
        entry = to_unicode(entry)
        entry = json.loads(entry)
    except:
        raise
    #We always lead with the bookid and the filename.
    mainfields = [str(bookid),to_unicode(entry['filename'])]
    #First, pull the unique variables and write them to the 'catalog' table
    for var in uniqueVariableNames:
        myfield = entry.get(var,"")
        mainfields.append(to_unicode(myfield))
    catalogtext = '\t'.join(mainfields) + "\n"
    catalog.write(catalogtext.encode('utf-8'))
    for var in arrayVariableNames:
        #Each of these has a different file it must write to... that's stored in the hash. (A good sign it should probably be a class, but oh well).
        outfile = arrayVariables[var]['output']
        lines = entry.get(var,[])
        for line in lines:
            writing = bookid+"\t"+line+"\n"
            outfile.write(writing.encode('utf-8'))
    bookid = bookid+1
    if bookid > 100:
        break
                        

#This must be run as a MySQL user with create_table privileges
cnx = MySQLdb.connect(read_default_file="~/.my.cnf",use_unicode = 'True',charset='utf8',db = "jstor")
cursor = cnx.cursor()
cursor.execute("SET NAMES 'utf8'")
cursor.execute("SET CHARACTER SET 'utf8'")

try:
    cursor.execute("CREATE DATABASE " + dbname)
except:
    print "Database " + dbname + " already exists: that might be intentional, so not dying"

cursor.execute("USE " + dbname)

try:
    "Setting up permissions for web user..."
    cursor.execute("GRANT SELECT ON " + dbname + ".*" + " TO '" + dbuser + "'@'%' IDENTIFIED BY '" + dbpassword + "'")
except:
    print "Something went wrong with the permissions"
    raise

def load_book_list():
    print "Making a SQL table to hold the catalog data"
    mysqlfields = ["bookid MEDIUMINT, PRIMARY KEY(bookid)","filename VARCHAR(255)","nwords INT"]
    for variable in uniqueVariables:
        createstring = variable.slowSQL()
        mysqlfields.append(createstring)
    #This creates the main (slow) catalog table
    createcode = """CREATE TABLE IF NOT EXISTS catalog (
        """ + ",\n".join(mysqlfields) + """
        );"""
    print createcode
    cursor.execute(createcode)
    #Never have keys before a LOAD DATA INFILE
    cursor.execute("ALTER TABLE catalog DISABLE KEYS")
    print "loading data into catalog using LOAD DATA LOCAL INFILE..."
    cursor.execute("""LOAD DATA LOCAL INFILE '../metadata/catalog.txt' 
                   INTO TABLE catalog
                   (bookid,filename,""" + ','.join([field.field for field in uniqueVariables]) + """) """)
    cursor.execute("ALTER TABLE catalog ENABLE KEYS")
    #If there isn't a 'searchstring' field, it may need to be coerced in somewhere hereabouts
    cursor.execute("UPDATE catalog SET nwords = (SELECT sum(count) FROM master_bookcounts WHERE master_bookcounts.bookid = catalog.bookid) WHERE nwords is null;");

def load_arrayVar_list(dfield):
    print "Making a SQL table to hold the data for " + dfield.name
    cursor.execute("""DROP TABLE IF EXISTS """ + dfield.name + ")")
    cursor.execute("""CREATE TABLE IF NOT EXISTS """ + dfield.name + """ (
        bookid MEDIUMINT, 
        """ +dfield.slowSQL() + """, PRIMARY KEY (bookid,""" +dfield.name + """)
        );""")
    cursor.execute("ALTER TABLE " + dbfield.name + " DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '../metadata/""" + dbfield.name +  """' 
                   INTO TABLE """ +dbfield.name + """ 
                   (bookid,""" + dbfield.name + """) """)
    cursor.execute("ALTER TABLE "+ dfield.name+"  ENABLE KEYS")

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
        wordid MEDIUMINT NOT NULL, INDEX (wordid,bookid,count),    
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

###This is the part that has to run on every startup.
def create_memory_tables():
    cursor.execute("DROP TABLE IF EXISTS tmp;");
    cursor.execute("""CREATE TABLE tmp
     (bookid MEDIUMINT, PRIMARY KEY (bookid),
      nwords MEDIUMINT,""" +",\n".join([term.sqlCreate() for term in arrayTerms]) + """
      """+ """)
    ENGINE=MEMORY;""");
    cursor.execute("INSERT INTO tmp SELECT bookid,nwords,day,week,month,tld,mld FROM catalog;");
    cursor.execute("DROP TABLE IF EXISTS fastcat;");
    cursor.execute("RENAME TABLE tmp TO fastcat;");

    cursor.execute("CREATE TABLE tmp (wordid MEDIUMINT, PRIMARY KEY (wordid), word VARCHAR(30), INDEX (word), casesens VARBINARY(30),UNIQUE INDEX(casesens)) ENGINE=MEMORY;")
    #For some reason, there are some duplicate keys; INSERT IGNORE skips those. It might be worth figuring out exactly how they creep in: it looks to me like it has to with unicode or other non-ascii characters,
    #so we may be losing a few of those here.
    cursor.execute("INSERT IGNORE INTO tmp SELECT wordid as wordid,word,casesens FROM words WHERE CHAR_LENGTH(word) <= 30 AND wordid <= 1500000 ORDER BY wordid;")
    cursor.execute("DROP TABLE IF EXISTS wordsheap;");
    cursor.execute("RENAME TABLE tmp TO wordsheap;");
    
    cursor.execute("CREATE TABLE tmp (bookid MEDIUMINT, subclass VARCHAR(18), PRIMARY KEY (bookid,subclass)) ENGINE=MEMORY ;");
    cursor.execute("INSERT into tmp SELECT bookid,subgenre FROM genre GROUP BY bookid,subgenre;");
    cursor.execute("DROP TABLE IF EXISTS subclass;");
    cursor.execute("RENAME TABLE tmp TO subclass;");
    
    cursor.execute("CREATE TABLE tmp (bookid MEDIUMINT, INDEX (bookid), archive VARCHAR(13)) ENGINE=MEMORY ;");
    cursor.execute("INSERT into tmp SELECT bookid, genre FROM genre GROUP BY bookid,genre;");
    cursor.execute("DROP TABLE IF EXISTS archive;");
    cursor.execute("RENAME TABLE tmp TO archive;");








#We'll need something like this eventually.

#    cursor.execute("DROP TABLE if exists column_options;");
#    cursor.execute("""CREATE TABLE column_options ENGINE=MEMORY 
#    SELECT TABLE_NAME,
#                 COLUMN_NAME,
#                 DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS   
#        WHERE TABLE_SCHEMA='arxiv';""");

#load_word_list()
create_unigram_book_counts()
create_bigram_book_counts()
load_book_list()
load_word_list()

#create_memory_tables()
