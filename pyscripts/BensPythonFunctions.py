#UNIVERSAL SETTINGS
import MySQLdb
import re
import subprocess
from subprocess import call
import os
from datetime import datetime

#CHAUCER SETTINGS:
if False:
    texts_directory = "/group/culturomics/books"
    downloads_directory = "/home/bschmidt/IA"
    mysql_directory = "/var/lib/mysql/data/presidio"
    cnx = None
    cursor = cnx.cursor()
    cursor.execute("SET NAMES 'utf8'")
    #import nltk
    import json
    from nltk import PorterStemmer
    from datetime import datetime
    project_directory = "/mnt/bschmidt/Internet_Archive" 
    texts_directory = ''
    

#WUMPUS SETTINGS:
if True:
    project_directory = '/home/bschmidt/Internet_Archive'
    texts_directory = '/group/culturomics/books'
    downloads_directory = '/group/culturomics/books/Downloads'
    mysql_directory = ''
    cnx = None
    cursor = cnx.cursor()
    cursor.execute("SET NAMES 'utf8'")

####### FUNCTIONS DEALING WITH WORD LISTS #######
def load_1grams_table(): #Get the onegrams lists of words into the database.
    import os
    cursor.execute("""CREATE TABLE 1grams (
        word VARCHAR(255), INDEX (word),
        year MEDIUMINT,
        words INT,
        pages INT,
        books INT);""")
    cursor.execute("""ALTER TABLE 1grams disable keys""")
    for file in os.listdir(downloads_directory + '/ngrams'):
        name = downloads_directory + '/ngrams/' + file
        cursor.execute("LOAD DATA LOCAL INFILE '" + name + "' INTO TABLE 1grams FIELDS TERMINATED BY '\t';")
    cursor.execute("""ALTER TABLE 1grams enable keys""")

def load_ngrams_word_list_as_new_sql_file(): #This is a version that has been parsed in perl to have common words.
    print "Loading ngrams wordlist as SQL file..."
    call("perl " + project_directory + "/perlscripts/ngramsparser.pl " + downloads_directory + '/ngrams',shell=True)
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS words (
        wordid MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, 
        word VARCHAR(255), INDEX (word),
        count BIGINT UNSIGNED,
        normcount FLOAT,
        books INT UNSIGNED,
        lowercase VARCHAR(255), INDEX (lowercase),
        stem VARCHAR(31), INDEX (stem),
        stopword TINYINT DEFAULT 0,
        include_in_counts TINYINT DEFAULT 0,
        charcode VARBINARY(32),
        ffix VARCHAR(255),
        casesens VARBINARY(255), INDEX(casesens),
        IDF FLOAT,
        PRIMARY KEY (wordid)
        );""")
    cursor.execute("ALTER TABLE words DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '""" + downloads_directory + "/sorted.txt" + """' INTO TABLE words (word,count,books,normcount,lowercase)""")
    print "building indexes"
    #Store the IDF values
    cursor.execute("""SET @a = (SELECT max(books) FROM words);""")
    cursor.execute("""UPDATE words SET IDF = log(@a/books);""")
    cursor.execute("ALTER TABLE words ENABLE KEYS")
    
def update_Porter_stemming(): #We use stems occasionally.
    "Updating stems from Porter algorithm..."
    from nltk import PorterStemmer
    stemmer = PorterStemmer()
    cursor.execute("""SELECT word FROM words WHERE wordid <= 750000 and stem is null;""")
    words = cursor.fetchall()
    for local in words:
        word = ''.join(local)
        if re.match("^[A-Za-z]+$",word):
            query = """UPDATE words SET stem='""" + stemmer.stem(''.join(local)) + """' WHERE word='""" + ''.join(local) + """';""" 
            z = cursor.execute(query)
        
def update_stopwords(): #I used to use this list of stopwords to keep some processes shorter
    "updating stopwords from nltk and my additions..."
    stopset = set(nltk.corpus.stopwords.words('english'))
    stopset.update(set(['one', 'may', 'would', 'upon', 'two', 'said', 'made', 'first', 'must', 'could', 'many', 'well', 'shall', 'much', 'like', 'us', 'also', 'every', 'without', 'even', 'part', 'make', 'place', 'found', 'people', 'way', 'three','never', 'yet', 'might', 'come', 'still', 'know', 'd', 'power', 'another', 'thus', 'last', 'right', 'though', 'take', 'given', 'called', 'de', 'came', 'however', 'among', 'give', 'far', 'present', 'whole', 'form', 'used', 'less', 'thought', 'use', 'name', 'year', 'left', 'order', 'back', 'always', 'ever', 'let', 'things', 'nothing', 'v', 'away', 'taken', 'p', 'per', 'therefore', 'whose', 'since', 'cannot', 'o', 'others', 'second', 'often', 'four', 'half', 'within','several', 'following', 'soon', 'almost','five','either', 'thing', 'b', 'st', 'hundred','whether', 'become', 'c', 'perhaps', 'n', 'enough', 'e']))
    import string
    letters = string.lowercase
    for lettera in letters:
        for letterb in letters:
            updated = lettera+letterb
            stopset.update([(updated)])
        stopset.update(lettera)
    for stopword in stopset:
        query = """UPDATE words SET stopword=1 WHERE word='""" + stopword + """';""" 
        z = cursor.execute(query)
        
####FUNCTIONS DEALING WITH LIBRARY CATALOGS#######

###CREATING CATALOGS
def create_catalog_table(latestOLcatalog = "2011-09-30"):
    print "Parsing Latest OL dump for editions data:"
    system_call = 'perl ' + project_directory+'/perlscripts/print\ OL\ works\ catalog\ to\ text\ file\ for\ import.pl ' + downloads_directory + '  ol_dump_editions_' + latestOLcatalog + '.txt ' +project_directory
    call(system_call ,shell=True)
    print "Building SQL tables"
    cursor.execute("""DROP TABLE IF EXISTS OL_editions""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OL_editions (
    authorid VARCHAR(15), INDEX (authorid), 
    editionid VARCHAR(15), INDEX (editionid),
    language CHAR(3),
    lc_classifications VARCHAR(23),
    lccn INT,
    ocaid VARCHAR(29), index (ocaid),
    oclc_numbers INT,
    publish_country CHAR(3),
    year SMALLINT,
    publish_places VARCHAR(127),
    publishers VARCHAR(127),
    title VARCHAR(255),
    workid VARCHAR(15), INDEX(workid),
    authorbirth SMALLINT,
    workyear SMALLINT,
    author VARCHAR(255)   ) 
    """)

    cursor.execute("LOAD DATA LOCAL INFILE '" + downloads_directory + "/Edition Data.txt" + "' INTO TABLE OL_editions (ocaid ,title ,publish_country , year , lc_classifications ,oclc_numbers ,    lccn ,    publish_places ,    publishers ,    language ,    editionid ,    authorid,    workid);")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS open_editions (
    bookid MEDIUMINT UNSIGNED AUTO_INCREMENT,
    authorid VARCHAR(15), INDEX (authorid),
    editionid VARCHAR(15), INDEX (editionid),
    language CHAR(3),
    lc_classifications VARCHAR(23),
    lccn INT,
    ocaid VARCHAR(29), index (ocaid),
    oclc_numbers INT,
    publish_country CHAR(3),
    year SMALLINT,
    publish_places VARCHAR(127),
    publishers VARCHAR(127),
    title VARCHAR(255),
    workid VARCHAR(15),INDEX(workid),
    authorbirth SMALLINT,
    workyear SMALLINT,
    author VARCHAR(255),
    nwords INT,
    ngrams INT,
    volume TINYINT,
    subset VARCHAR(31), INDEX (subset),
    country VARCHAR(255),
    state CHAR(2),
    author_age SMALLINT,
    city VARCHAR(255),
    lc0 CHAR(1),
    lc1 CHAR(2),
    lc2 SMALLINT,
    PRIMARY KEY (bookid)
    ) CHARACTER SET 'utf8';    """)
    cursor.execute("""DROP TABLE IF EXISTS derivedCatalog""")
    cursor.execute("""
    CREATE TABLE derivedCatalog (
    bookid MEDIUMINT AUTO_INCREMENT,
    editionid VARCHAR(15), INDEX (editionid),
    nwords INT,
    ngrams INT,
    volume TINYINT,
    subset VARCHAR(31), INDEX (subset),
    country VARCHAR(255),
    state CHAR(2),
    author_age SMALLINT,
    city VARCHAR(255),
    lc0 CHAR(1),
    lc1 CHAR(2),
    lc2 SMALLINT,
    aLanguage VARCHAR(31),
    duplicate TINYINT,
    PRIMARY KEY (bookid)
    ) CHARACTER SET 'utf8';""")
    print "Filling a catalog with derived variables"
    cursor.execute("""CREATE TABLE IF NOT EXISTS bookid_master (bookid MEDIUMINT AUTO_INCREMENT,editionid VARCHAR(15), INDEX (editionid),PRIMARY KEY (bookid))""")
    cursor.execute("""INSERT INTO bookid_master (bookid,editionid)
                      SELECT t1.bookid,t1.editionid from open_editions as t1 LEFT JOIN bookid_master
                      USING (bookid) where bookid_master.bookid is null;""")
    cursor.execute("""
    INSERT INTO derivedCatalog (SELECT bookid,editionid,nwords,ngrams,volume,subset,country,state,author_age,city,lc0,lc1,lc2,aLanguage,duplicate FROM open_editions);""")
    cursor.execute("""DROP TABLE IF EXISTS master_catalog""")
    cursor.execute("""CREATE TABLE master_catalog (SELECT * FROM OL_editions LEFT JOIN derivedCatalog USING (editionid))""")
    cursor.execute("""ALTER TABLE master_catalog DISABLE KEYS""")
    for mystring in ["ocaid","bookid","editionid","subset","lc_classifications"]:
        cursor.execute("""ALTER TABLE master_catalog ADD INDEX (""" + mystring + """)""")
    cursor.execute("""ALTER TABLE master_catalog ENABLE KEYS""")
    #I twice update the catalog against the master bookid list, because it will create a mess if we get multiple entries in there.
    cursor.execute("""UPDATE master_catalog as t1, bookid_master as t2 SET t1.bookid = t2.bookid WHERE t1.editionid = t2.editionid and t1.bookid is null;""")
    cursor.execute("""INSERT INTO bookid_master (editionid)
                      (SELECT master_catalog.editionid FROM master_catalog LEFT JOIN bookid_master USING (editionid) WHERE bookid_master.bookid is null)""")
    cursor.execute("""UPDATE master_catalog as t1, bookid_master as t2 SET t1.bookid = t2.bookid WHERE t1.editionid = t2.editionid and t1.bookid is null;""")
    #cursor.execute("""DROP TABLE IF EXISTS open_editions""")
    #cursor.execute("""RENAME TABLE master_catalog TO open_editions;""")
    add_author_dates(latestOLcatalog=latestOLcatalog,downloads_directory = downloads_directory+"/Catinfo")
    add_work_dates(latestOLcatalog=latestOLcatalog,downloads_directory = downloads_directory+"/Catinfo")
    add_split_lc_fields()

def create_editions_table(editionsloc = downloads_directory + "/OL_Subject_Headings.txt"):
    queryString = """
     CREATE TABLE IF NOT EXISTS subject_headings (
     editionid VARCHAR(15),
     h1 VARCHAR(2045), INDEX (h1),
     h2 VARCHAR(255), INDEX (h2),
     h3 VARCHAR(255), INDEX (h3),
     h4 VARCHAR(255),
     h5 VARCHAR(255),
     h6 VARCHAR(255),
     h7 VARCHAR(255),
     h8 VARCHAR(255),
     bookid MEDIUMINT UNSIGNED, INDEX (bookid)
     ) CHARACTER SET 'utf8';    """
    print queryString
    cursor.execute(queryString)
    cursor.execute("""ALTER TABLE subject_headings DISABLE KEYS""")
    cursor.execute("""LOAD DATA LOCAL INFILE '""" + editionsloc + """' INTO TABLE subject_headings""")
    cursor.execute("""UPDATE subject_headings SET bookid = (SELECT open_editions.bookid from open_editions where open_editions.editionid=subject_headings.editionid)""")
    print "enabling keys"
    queryString = """
     CREATE TABLE IF NOT EXISTS subjectsheap (
     h1 VARCHAR(40), INDEX (h1),
     h2 VARCHAR(35), INDEX (h2),
     h3 VARCHAR(20), INDEX (h3),
     bookid MEDIUMINT UNSIGNED, INDEX (bookid)
     ) CHARACTER SET 'utf8' ENGINE = MEMORY;    """

    cursor.execute("""ALTER TABLE subject_headings ENABLE KEYS;""")

def add_author_dates (latestOLcatalog="2011-04-30",downloads_directory = ""):
    print "ADDING AUTHOR DATES..."
    filehandle  = open(downloads_directory + "/ol_dump_authors_"+ latestOLcatalog + ".txt",'r')
    authorlist = set()
    print "Loading information from catalog to parse..."
    cursor.execute("SELECT authorid,editionid FROM OL_editions WHERE author is NULL")
    print "Storing catalog information..."
    for entry in cursor:
        authorlist.add(entry[0])
    print "Loading information from file into database..."
    for myline in filehandle:
        myline = myline.split("\t")
        id = re.sub(".*/","",myline[1])
        if id in authorlist:
            info = json.loads(myline[4])
            name = ""
            birth = "NULL"
            if ('name' in info):
                name = info['name']
                name = mysql_protect(name)
            if 'birth_date' in info:
                birth = info['birth_date']
                birth = extract_year(birth)
            if name != "":
                sql_string = 'UPDATE OL_editions SET author="' +name+ '", authorbirth='+birth+' WHERE authorid="' + id + '"'
                cursor.execute(sql_string) 
   
def add_work_dates (latestOLcatalog="2011-07-31",downloads_directory = "/home/bschmidt/IA/Catinfo"):
    print "ADDING WORK DATES..."
    filehandle  = open(downloads_directory + "/ol_dump_works_"+ latestOLcatalog + ".txt",'r')
    authorlist = set()
    print "Loading information from catalog to parse..."
    cursor.execute("SELECT workid,editionid FROM OL_editions where workyear is NULL")
    print "Storing catalog information..."
    for entry in cursor:
        authorlist.add(entry[0])
    print "Loading information from file into database..."
    for myline in filehandle:
        myline = myline.split("\t")
        workid = re.sub(".*/","",myline[1])
        if workid in authorlist:
            info = json.loads(myline[4])
            year = "NULL"
            if 'first_publish_date' in info:
                year = info['first_publish_date']
                year = extract_year(year)
            sql_string = 'UPDATE OL_editions SET workyear='+year+' WHERE workid="' + workid + '"'
            cursor.execute(sql_string) 

def mysql_protect(string):
    #Occasionaly, I insert queries into MySQL that have unpermitted text characters in them. This should fix that.
    text = string.replace('''\\''','''\\\\''')
    text = text.replace('"','\\"')
    return text

def add_split_lc_fields():
    print "loading classification data to parse"
    lcclasses = get_dict_from_mysql("SELECT editionid,lc_classifications FROM open_editions WHERE lc_classifications NOT LIKE '' and lc1 is null;")
    print "Splitting and saving LC codes"
    for edition in lcclasses.keys():
        lcclass = lcclasses[edition]
        lcclass = lcclass.encode("ascii",'replace')
        mymatch = re.match(r"^(?P<lc1>[A-Z]+) ?(?P<lc2>\d+)", lcclass)
        if (mymatch):
            silent = cursor.execute("UPDATE open_editions SET lc1='"+mymatch.group('lc1')+"',lc2="+mymatch.group('lc2')+" WHERE editionid='" + edition + "';")
    print "Indexing LC codes"
    cursor.execute("ALTER TABLE open_editions add index lc1 (lc1);")

def create_memory_tables():
    cursor.execute("drop table if exists tmpheap")
    cursor.execute("""CREATE TABLE tmpheap (
        wordid MEDIUMINT UNSIGNED NOT NULL,
        word VARCHAR(31), INDEX(word),
        stem VARCHAR(31), INDEX(stem),
        casesens VARBINARY(31), INDEX (casesens),
        ffix VARCHAR(31), INDEX (ffix),
        IDF FLOAT,
        PRIMARY KEY (wordid)) ENGINE = MEMORY""")
    cursor.execute("""INSERT INTO tmpheap SELECT wordid,word,stem,casesens,ffix,IDF FROM words where wordid <= 700000;""")
    cursor.execute("drop table if exists wordsheap")
    cursor.execute("RENAME TABLE tmpheap to wordsheap")
    cursor.execute("""CREATE TABLE tmpheap (
        bookid MEDIUMINT UNSIGNED,
        year SMALLINT,
        lc1 CHAR(3), INDEX(lc1),
        lc2 SMALLINT, INDEX(lc2),
        nwords INT,
        publish_country CHAR(3),
        authorbirth SMALLINT,
        workyear SMALLINT,
        language CHAR(3),
        subset VARCHAR(31), INDEX (subset),
        country VARCHAR(10),
        state CHAR(2),
        author_age SMALLINT,
        lc0 CHAR(1),
        month MEDIUMINT,
        PRIMARY KEY (bookid)) ENGINE = MEMORY""")
    cursor.execute("""INSERT INTO tmpheap SELECT bookid,year,lc1,lc2,nwords,publish_country,authorbirth,workyear,language,subset,country,state,author_age,lc0,TO_DAYS(MAKEDATE(year,1)) FROM open_editions WHERE nwords >0  AND duplicate != 1; """)
    cursor.execute("""update tmpheap set subset='beta'""")
    cursor.execute("""DROP TABLE IF EXISTS catalog""")
    cursor.execute("RENAME TABLE tmpheap TO catalog")
    #Drop some duplicate journals, which usually have a period at the end of the name.
    cursor.execute("""UPDATE catalog set bflag=0;""")
    cursor.execute("""UPDATE catalog JOIN (SELECT * FROM open_editions as o2 JOIN (SELECT title,year,count(*) as count FROM open_editions WHERE nwords > 0 AND title LIKE "%." AND title NOT LIKE "%ouvre%" and title NOT LIKE "%works%" AND title NOT like "Trait%" GROUP BY title,year HAVING count > 8) as journal USING (title,year)) as tmp ON (tmp.bookid=catalog.bookid) SET bflag=1;""")
    cursor.execute("""DELETE FROM catalog WHERE bflag=1;""")


##### FUNCTIONS DEALING WITH WORDCOUNT TABLES

def fix_place_metadata():
    print "Updating US and UK"
    cursor.execute("update open_editions set country = 'USA' WHERE country is null and SUBSTR(publish_country,3,1)='u';")
    cursor.execute("update open_editions set country = 'UK' WHERE SUBSTR(publish_country,3,1)='k' and country is null;")
    cursor.execute("update open_editions set state = publish_country WHERE SUBSTR(publish_country,3,1)='u' and state is null;")
    print "Updating common country codes"
    codes = {"ne":"Netherlands","au":"Austria","be":"Belgium", "ii":"India",'sz':"Switzerland","dk":"Denmark","po":"Portugal", "pl":"Poland","ru":"Russia","sw":"Sweden"}
    for code in codes:
        print "\t" + code
        cursor.execute("UPDATE open_editions set country = '" + codes[code] + "' WHERE publish_country = '" + code + "' and country is null")
    World_Cities = {"Oxford":"UK", "London":"UK", "Paris":"France","Leipzig":"Germany","Berlin":"Germany", "Tokyo":"Japan","Edinburgh":"UK","Lisboa":"Portugal","Bruxelles":"Belgium", "Madrid":"Spain","Wien":"Austria","Milano":"Italy","Budapest":"Hungary","Stuttgart":"Germany","Buenos Aires":"Argentina","Firenze":"Italy","Lipsiae":"Germany"}
    print "Fixing word Cities"
    for city in World_Cities.keys():
        print "\t" + city
        versions = ["_" + city,city,city+"%","_"+city+"%"]
        for version in versions:
            cursor.execute("UPDATE open_editions SET country = '" + World_Cities[city] + "' WHERE country is null and publish_places LIKE '" + version + "'")
    US_Cities = {"New York":"NY","New-York":"NY","Cincinatti":"OH","Boston":"MA","Chicago":"IL","Philadelphia":"PA"}
    print "Fixing US cities"
    for city in US_Cities.keys():
        print "\t" + city
        versions = ["_" + city,city,city+"%","_"+city+"%"]
        for version in versions:
          cursor.execute("UPDATE open_editions SET country = 'USA' WHERE country is null and publish_places LIKE '" + version + "'")  
          cursor.execute("UPDATE open_editions SET state = '" + US_Cities[city] + "' WHERE state is null and publish_places LIKE '" + version + "'")

def alert_duplicate_editions():
    #This doesn't match the open library spec, but they have a lot of duplicate editions. So I only allow one copy of every workid-year combination.
    cursor.execute("""DROP TABLE IF EXISTS duplicates""")
    print "Finding duplicates based on workid and year"
    cursor.execute("""CREATE TABLE duplicates (bookid MEDIUMINT UNSIGNED) ENGINE=MEMORY;""")
    cursor.execute("""INSERT INTO duplicates SELECT t1.bookid FROM open_editions t1 JOIN open_editions t2 USING (year,workid) WHERE workid is not null and workid != "" and t1.nwords > 0 and t2.nwords > 0 AND t1.bookid > t2.bookid GROUP BY t1.bookid;""")
    print "updating open_editions table"
    cursor.execute("""UPDATE open_editions SET duplicate=0""")
    cursor.execute("""UPDATE open_editions as t1 , duplicates as t2 SET t1.duplicate=1 where t1.bookid = t2.bookid""")
    cursor.execute("""DROP TABLE duplicates""")

def create_counts_and_indexes(libname,mysql_directory):
    create_counts(libname)
    create_indexes(libname,mysql_directory)

def create_counts(libname):
    print str(datetime.now()) + "\tGetting list of bookids to read..."
    bookids = get_dict_from_mysql("SELECT bookid,ocaid FROM catalog WHERE "+libname+"=1;")
    print str(datetime.now()) + "\tGetting wordlists to process with..."
    allwords = get_dict_from_mysql("SELECT word,wordid FROM words WHERE wordid < 200000")
    shortwords = get_dict_from_mysql("SELECT word,wordid FROM words WHERE stopword=0 AND wordid < 200000")
    print str(datetime.now()) + "\tDoing Word Counts"
    count_words(libname,bookids,allwords,shortwords)
    
def download_texts(filelists,directory="/srv/books",fileloc="todownload.txt"):
    import os
    import os.path
    import urllib
    for catname in filelists:
        files = []
        for line in open("/mnt/bschmidt/" + catname):
            line = line.rstrip()
            files.append(line)
        print "Getting ready to read " + str(len(files)) + " files from " + catname
        i = 0
        for file in files:
            i = i+1
            fileloc = directory + "/" + file + ".txt"
            if not os.path.exists(fileloc) and not os.path.exists(directory + "/zipped/" + file + ".txt.gz"):
                try:
                    WRITE = open(fileloc,'w')
                    print "working on " + file + " (" + str(i*1000/len(files)) + " permille done)" 
                    CON = urllib.urlopen("http://www.archive.org/download/"+file+"/"+file+"_djvu.txt")
                    data = CON.read()
                    WRITE.write(data)
                    CON.close()
                    WRITE.close()
                    del CON
                    del WRITE
                except:
                    pass

def fill_db():
    subsets = get_subsets_list() #We are going to store blocks of about 10 - 500 000 books in files. They will probably just be flat text files in a directory: we could also just query the database for them.
    for subset in ['DPLA','DPLANYNY']: #obviously should be "subsets" if you're just flying through
        print 'working on subset' + subset
        ocaids = get_filenames_list_for_subset(subset)
        create_counttable(subset,"bookcounts") #for now, just a _bookcounts table
        for ocaid in ocaids:
            upload_book_counts(ocaid,subset+"_bookcounts")
        #pack_tables([subset + "_bookcounts" for subset in subsets])
        #enable_indexes(subset)
    #build_merge_tables()

def get_filenames_list_for_subset(subset):
    cursor.execute("SELECT ocaid from open_editions WHERE subset='" + subset + "'")
    mylist = cursor.fetchall()
    #This ugly bit of code makes a list from the first column of mysql results
    return [z for z in [a[0] for a in mylist] if z!=None]

def get_subsets_list():
    cursor.execute("SELECT subset from open_editions GROUP BY subset")
    p = cursor.fetchall()
    return [z for z in [a[0] for a in p] if z!=None]

def upload_book_counts(ocaid,destination_table):
    #This has to be run from the server where the files are: so currently, it gets called from Wumpus
    if os.path.exists(texts_directory + "/encoded/1grams/" + ocaid[0] + "/" + ocaid + ".txt"):
        try: 
            cursor.execute("LOAD DATA LOCAL INFILE '" + texts_directory + "/encoded/1grams/" + ocaid[0] + "/" + ocaid + ".txt" + "' INTO TABLE " + destination_table + " FIELDS TERMINATED BY ' '")
        except:
            print "failure on uploading from " + ocaid
    else:
        #NOTE: THIS DOESN'T DO THE RIGHT THING IF TWO bookid FIELDS HAVE THE SAME ocaid, WHICH MAY HAPPEN
        cursor.execute("UPDATE open_editions SET nwords=0 WHERE ocaid='" + ocaid + "'")

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
        count MEDIUMINT UNSIGNED NOT NULL) ENGINE = """ + engine + """;"""
    if tabletype=="sentencecounts":
        query = """CREATE TABLE IF NOT EXISTS """ + tablename + """ (
        bookid MEDIUMINT NOT NULL, INDEX (bookid,sentencenum,wordid,count),
        sentencenum MEDIUMINT NOT NULL, INDEX (bookid,wordid,sentencenum,count),
        wordid MEDIUMINT NOT NULL, INDEX (wordid,bookid,sentencenum,count),
        count SMALLINT UNSIGNED NOT NULL) ENGINE = """ + engine + """;"""
    if tabletype=="booktext":
        query = """CREATE TABLE IF NOT EXISTS""" + tablename + """ (
        bookid MEDIUMINT NOT NULL, INDEX (bookid,sentencenum),
        sentencenum MEDIUMINT NOT NULL, 
        sentence TEXT) ENGINE = """ + engine + """;"""
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
