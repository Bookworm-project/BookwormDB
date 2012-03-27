#!/usr/bin/python
# -*- coding: utf-8 -*-

# Be sure that txtdir, catfile, and metafile are set correctly

import MySQLdb

#txtdir = "/scratch/global/neva/texts/"
txtdir = "/media/troilus/arxiv/"
catfile = "catalog.txt"
metafile = "new_metadata.txt"

cnx = MySQLdb.connect(read_default_file="~/.my.cnf",use_unicode = 'True',charset='utf8',db = "arxiv")
cursor = cnx.cursor()
cursor.execute("SET NAMES 'utf8'")
cursor.execute("SET CHARACTER SET 'utf8'")

def load_word_list():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS words (
        wordid MEDIUMINT, 
        word VARCHAR(255), INDEX (word),
        count BIGINT UNSIGNED
        );""")
    cursor.execute("ALTER TABLE words DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '"""
                   +txtdir+"""wordlist/wordlist.txt' 
                   INTO TABLE words
                   CHARACTER SET binary
                   (wordid,word,count) """)
    cursor.execute("ALTER TABLE words ENABLE KEYS")

def create_unigram_book_counts():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS master_bookcounts (
        bookid MEDIUMINT NOT NULL, INDEX(bookid,wordid,count),
        wordid MEDIUMINT NOT NULL, INDEX (wordid,bookid,count),    
        count MEDIUMINT UNSIGNED NOT NULL);""")
    cursor.execute("ALTER TABLE master_bookcounts DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    for line in open(txtdir+catfile):
        fields = line.split()
        try:
            cursor.execute("LOAD DATA LOCAL INFILE '" +txtdir+"encoded/unigrams/"+fields[1]+".txt' INTO TABLE master_bookcounts CHARACTER SET utf8 (wordid,count) SET bookid="+fields[0]);
        except:
            pass
    cursor.execute("ALTER TABLE master_bookcounts ENABLE KEYS")

def create_bigram_book_counts():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS master_bigrams (
        bookid MEDIUMINT NOT NULL, 
        word1 MEDIUMINT NOT NULL, INDEX (word1,word2,bookid,count),    
        word2 MEDIUMINT NOT NULL,     
        count MEDIUMINT UNSIGNED NOT NULL);""")
    cursor.execute("ALTER TABLE master_bigrams DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    for line in open(txtdir+catfile):
        fields = line.split()
        try:
            cursor.execute("LOAD DATA LOCAL INFILE '" +txtdir+"encoded/bigrams/"+fields[1]+".txt' INTO TABLE master_bigrams (word1,word2,count) SET bookid="+fields[0]);
        except:
            pass
    cursor.execute("ALTER TABLE master_bigrams ENABLE KEYS")

def load_book_list():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS catalog (
        bookid MEDIUMINT, PRIMARY KEY(bookid),
        arxivid VARCHAR(255),
        email VARCHAR(255),
        date DATETIME,
        title VARCHAR(255),
        author VARCHAR(255),
        genre VARCHAR(255)
        );""")
    cursor.execute("ALTER TABLE catalog DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '"""
                   +txtdir+metafile+"""' 
                   INTO TABLE catalog
                   (bookid,arxivid,email,date,title,author,genre) """)
    cursor.execute("ALTER TABLE catalog ENABLE KEYS")

def load_genre_list():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS genre (
        bookid MEDIUMINT, 
        genre VARCHAR(255),
        subgenre VARCHAR(255)
        );""")
    cursor.execute("ALTER TABLE genre DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '"""
                   +txtdir+metafile+ """' 
                   INTO TABLE genre
                   (bookid,genre,subgenre) """)
#                   (bookid,@dummy,@dummy,@dummy,@dummy,genre) """)
    cursor.execute("ALTER TABLE genre ENABLE KEYS")

### THIS STUFF ONLY GETS ADDED ONCE!!!!!!!!!!!!!!!!!!!!! 
### There's another section below that gets redone every time we startup 
### the server. 
def set_nwords_domains():
    cursor.execute("ALTER TABLE catalog ADD nwords INT;");
    cursor.execute("UPDATE catalog SET nwords = (SELECT sum(count) FROM master_bookcounts WHERE master_bookcounts.bookid = catalog.bookid) WHERE nwords is null;");
   #mld is for medium level domain; we need SECOND AND third level domains to get it to work properly with japanese and british institutions.
    cursor.execute("ALTER TABLE catalog ADD (day MEDIUMINT, week MEDIUMINT,month MEDIUMINT, tld VARCHAR(6), sld VARCHAR(25), ld3 VARCHAR(31), mld VARCHAR(31);");
    cursor.execute("UPDATE catalog SET day=TO_DAYS(date), week = ROUND(TO_DAYS(date)/7)*7, month = TO_DAYS(STR_TO_DATE(DATE_FORMAT(date, '01 %M %Y'),'%d %M %Y'));");

#SQL, it turns out, was an insane way to try to set e-mail domains without using regular expressions. But it works.
    cursor.execute("""UPDATE catalog SET
     tld=    REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',1)),
     sld = SUBSTR(REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',2)),LOCATE('@',REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',2)))+1,LENGTH(REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',2)))),
ld3 = SUBSTR(REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',3)), LOCATE('@',REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',3)))+1,
LENGTH(REVERSE(SUBSTRING_INDEX(REVERSE(REPLACE(email,'>','')),'.',3))));""");

    cursor.execute("UPDATE catalog SET mld=sld;");
    cursor.execute("UPDATE catalog SET mld=ld3 WHERE  sld REGEXP '^(ac|edu)';");

###This is the part that has to run on every startup.
def create_memory_tables():
    cursor.execute("DROP TABLE IF EXISTS tmp;");
    cursor.execute("""CREATE TABLE tmp
     (bookid MEDIUMINT, INDEX (bookid),
      nwords MEDIUMINT,
      day MEDIUMINT,
      week MEDIUMINT,
      month MEDIUMINT,
      tld CHAR(3),
      mld VARCHAR(15))
    ENGINE=MEMORY;""");
    cursor.execute("INSERT INTO tmp SELECT bookid,nwords,day,week,month,tld,mld FROM catalog;");
    cursor.execute("DROP TABLE IF EXISTS fastcat;");
    cursor.execute("RENAME TABLE tmp TO fastcat;");

    cursor.execute("CREATE TABLE tmp (wordid MEDIUMINT, INDEX(wordid), word VARCHAR(30), INDEX (word), casesens VARBINARY(30),INDEX(casesens)) ENGINE=MEMORY;
INSERT INTO tmp SELECT wordid,word,casesens FROM words WHERE CHAR_LENGTH(word) <= 30 LIMIT 1500000;");
    cursor.execute("DROP TABLE IF EXISTS wordsheap;");
    cursor.execute("RENAME TABLE tmp TO wordsheap;");
    
    cursor.execute("CREATE TABLE tmp (bookid MEDIUMINT, subclass VARCHAR(18)) ENGINE=MEMORY ;");
    cursor.execute("INSERT into tmp SELECT bookid,subgenre FROM genre GROUP BY bookid,subgenre;");
    cursor.execute("ALTER TABLE tmp ADD INDEX (bookid);");
    cursor.execute("DROP TABLE IF EXISTS subclass;");
    cursor.execute("RENAME TABLE tmp TO subclass;");
    
    cursor.execute("CREATE TABLE tmp (bookid MEDIUMINT, INDEX (bookid), archive VARCHAR(13)) ENGINE=MEMORY ;");
    cursor.execute("INSERT into tmp SELECT bookid, genre FROM genre GROUP BY bookid,genre;");
    cursor.execute("DROP TABLE IF EXISTS archive;");
    cursor.execute("RENAME TABLE tmp TO archive;");

    cursor.execute("DROP TABLE if exists column_options;");
    cursor.execute("""CREATE TABLE column_options ENGINE=MEMORY 
    SELECT TABLE_NAME,
                 COLUMN_NAME,
                 DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS   
        WHERE TABLE_SCHEMA='arxiv';""");

#load_word_list()
#create_unigram_book_counts()
#create_bigram_book_counts()
#load_book_list()
#load_genre_list()
#set_nwords_domains()
create_memory_tables()
