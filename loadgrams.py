#UNIVERSAL SETTINGS
import MySQLdb
import re
import subprocess
from subprocess import call
import os
from datetime import datetime

#WUMPUS SETTINGS:
if True:
    project_directory = '/home/bschmidt/Internet_Archive'
    texts_directory = '/group/culturomics/books'
    downloads_directory = '/group/culturomics/books/Downloads'
    mysql_directory = ''
    cnx = MySQLdb.connect(host='melville.seas.harvard.edu',user='bschmidt',passwd='newton',db='presidio',use_unicode = 'True',charset='utf8')
    cursor = cnx.cursor()
    cursor.execute("SET NAMES 'utf8'")

def fill_db():
    subsets = get_subsets_list() #We are going to store blocks of about 10 - 500 000 books in files. They will probably just be flat text files in a directory: we could also just query the database for them.
    for subset in ['etc','fre','ger']: #obviously should be "subsets" if you're just flying through
        print 'Reading Values to input from ' + subset
        bookids = get_dict_from_mysql("SELECT ocaid,bookid from open_editions WHERE subset='" + subset + "'")
        print "Creating count table"
        create_counttable(subset,"bookcounts") #for now, just a _bookcounts table
        for ocaid in bookids.keys():
            if len(ocaid) > 0:
                upload_book_counts(ocaid,subset+"_bookcounts",bookids[ocaid])
        #pack_tables([subset + "_bookcounts" for subset in subsets])
        #enable_indexes(subset)
    #build_merge_tables()

def fill_bigrams():
    subsets = get_subsets_list() #We are going to store blocks of about 10 - 500 000 books in files. They will probably just be flat text files in a directory: we could also just query the database for them.
    for subset in ['eng','uuu','fre','etc']: #obviously should be "subsets" if you're just flying through
        print 'Reading Values to input from ' + subset
        bookids = get_dict_from_mysql("SELECT ocaid,bookid from open_editions WHERE subset='" + subset + "'")
        print "Creating count table"
        create_counttable(subset,"bigrams") #for now, just a _bookcounts table
        for ocaid in bookids.keys():
            if len(ocaid) > 0:
                upload_book_counts(ocaid,subset+"_bigrams",bookids[ocaid],'bigrams')
        #pack_tables([subset + "_bookcounts" for subset in subsets])
        #enable_indexes(subset)
    #build_merge_tables()

def get_filenames_list_for_subset(subset):
    mylist = cursor.fetchall()
    #This ugly bit of code makes a list from the first column of mysql results
    return [z for z in [a[0] for a in mylist] if z!=None]

def get_subsets_list():
    cursor.execute("SELECT subset from open_editions GROUP BY subset")
    p = cursor.fetchall()
    return [z for z in [a[0] for a in p] if z!=None]

def upload_book_counts(ocaid,destination_table,bookid,type='unigrams'):
    #This has to be run from the server where the files are: so currently, it gets called from Wumpus
    if os.path.exists(texts_directory + "/encoded/" + type + "/" + ocaid[0] + "/" + ocaid + ".txt"):
        if type=='unigrams':
            fields = "wordid,count"
        if type=='bigrams':
            fields = 'word1,word2,count'
        query = "LOAD DATA LOCAL INFILE '" + texts_directory + "/encoded/" + type + "/" + ocaid[0] + "/" + ocaid + ".txt" + "' INTO TABLE " + destination_table + " FIELDS TERMINATED BY '\t' (" + fields + ") SET bookid = '" + str(bookid) + "';"
        try: 
            cursor.execute(query)
        except:
            print "failure on uploading from " + ocaid; print query
    else:
        cursor.execute("UPDATE open_editions SET nwords=0 WHERE bookid=" + str(bookid) + "")
        

def pack_tables(tablenames):
    pass

def enable_indexes(tablenames):
    pass

def build_merge_tables():
    pass

def get_dict_from_mysql(query):
    #turns a MySQL query into a set of key-value pairs. Super-useful, super-easy.
    cursor.execute(query)
    mydict = dict(cursor.fetchall())
    return mydict
    
def create_counttable(libname,tabletype,suffix="",engine = "MYISAM",disable_keys = True):
    tablename = libname+"_"+tabletype+str(suffix)
    if tabletype=="bookcounts":
        query = """CREATE TABLE IF NOT EXISTS """ + tablename + """ (
        bookid MEDIUMINT NOT NULL, INDEX(bookid,wordid,count),
        wordid MEDIUMINT NOT NULL, INDEX (wordid,bookid,count),
        count MEDIUMINT UNSIGNED NOT NULL
                ) ENGINE = """ + engine + """;"""
    if tabletype=="sentencecounts":
        query = """CREATE TABLE IF NOT EXISTS """ + tablename + """ (
        bookid MEDIUMINT NOT NULL, INDEX (bookid,sentencenum,wordid,count),
        sentencenum MEDIUMINT NOT NULL, INDEX (bookid,wordid,sentencenum,count),
        wordid MEDIUMINT NOT NULL, INDEX (wordid,bookid,sentencenum,count),
        count SMALLINT UNSIGNED NOT NULL) ENGINE = """ + engine + """;"""
    if tabletype=="booktext":
        query = """CREATE TABLE IF NOT EXISTS """ + tablename + """ (
        bookid MEDIUMINT NOT NULL, INDEX (bookid,sentencenum),
        sentencenum MEDIUMINT NOT NULL, 
        sentence TEXT) ENGINE = """ + engine + """;"""
    if tabletype=="bigrams":
        query = """CREATE TABLE IF NOT EXISTS """ + tablename + """ (
        bookid MEDIUMINT NOT NULL, INDEX (bookid,word2,word1,count),
        word1 MEDIUMINT NOT NULL,
        word2 MEDIUMINT NOT NULL, INDEX (word2,word1,bookid,count),
        count MEDIUMINT NOT NULL) ENGINE = """ + engine + """;"""
    cursor.execute(query)
    if disable_keys:
        cursor.execute("ALTER TABLE " + tablename + " DISABLE KEYS;")
    
def create_mergetable(libname,tabletype,component_tables):
    create_counttable(libname,tabletype,suffix = "",engine = """MERGE UNION=(
    """ + ','.join(component_tables) + """)
    INSERT_METHOD = NO""",disable_keys=False)

def build_longset_merge():
    for type in ['bookcounts','sentencecounts','booktext']:
        cursor.execute("DROP TABLE IF EXISTS longset_" + type)
        component_tables = get_matching_tables(type + "\d+")
        cursor.execute("create table longset_" + type + " like " + component_tables[0])#The format is like any of the members, which must be identical
        cursor.execute("alter table longset_" + type + " engine=merge union(" + ','.join(component_tables) + ")")#And then we fill it with links to the members.

def build_merge_tables(libname):
    for type in ["bookcounts","booktext","sentencecounts"]:
        component_tables = get_matching_tables(libname+"_"+type)
        create_mergetable(libname,type,component_tables)

def enable_indexes(libname):
    for type in ["bookcounts","booktext","sentencecounts"]:
        print str(datetime.now()) + "\tBUILDING INDEXES ON " + type
        tablelist = get_matching_tables(libname + "_" + type)
        for table in tablelist:
            cursor.execute("ALTER TABLE " + table + " ENABLE KEYS")

def myisam_pack(libname,mysql_directory):
    #Compressing tables saves a lot of space (usually down to 33%) but requires that they be read only. 
    for type in ["bookcounts","sentencecounts"]:
        print str(datetime.now()) + "\tPACKING TABLES IN " + type
        tablelist = get_matching_tables(libname + "_" + type)
        for table in tablelist:
            call( "myisampack -s " + mysql_directory + "/" + table + ".MYI",shell=True)
#            call( "myisamchk -rq " + mysql_directory + "/" + table + ".MYI",shell=True) #This seems to screw things up somehow, so I don't call it anymore


def get_matching_tables(searchstring):
    #This can be helpful to check if tables exists for various reasons
    silent = cursor.execute("show tables;")
    tablelist = [item[0] for item in cursor.fetchall()]
    tablelist = filter(re.compile(searchstring).search,tablelist)
    return tablelist

#####GENERAL TEXT PROCESSING

def extract_year(string):
    years = re.findall("\d\d\d\d",string)
    if(years):
        return years[0]
    else:
        return "NULL"

def reload():
    execfile(project_directory+ "/pyscripts/Pyfunctions.py")

class SQLquery:
    def __init__(self,querystring):
        self.query = querystring
    def execute(self):
        cursor.execute(self.query)
        self.results = cursor.fetchall()
    def display(self):
        self.execute()
        for line in self.results:
            print "\t".join([str(element) for element in line])
            

#######GENERAL SQL FUNCTIONS

def MySQL_insert(table,columns,data):
    #Note: I'm taking data as a list of strings, since a list of lists would create all sorts of funny typing problems with numbers and characters
    string = """INSERT INTO """ + table + "(" + columns + ") " + "VALUES " + ", ".join(data)
    return string

def populate_table(sqltable,file,fields,directory,elements_at_a_time=1000):
    pass
    #Everything I did here, I'm now doing with load data infile

def delete_matching_database_tables(string): #Dangerous!
    tablelist = get_matching_tables(string)
    for table in tablelist:
       cursor.execute("drop table " + table)
            
#### NOTEPAD
def update_word_counts():
    cursor.execute("""update open_editions set nwords = (select sum(count) as count from sprint_bookcounts where open_editions.bookid = sprint_bookcounts.bookid) WHERE subset='sprint';""")
    #This updates the open_editions nwords field from the database itself--quite a nice way to do it.
