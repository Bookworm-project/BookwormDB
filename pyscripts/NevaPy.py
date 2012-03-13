#!/usr/bin/python
# -*- coding: utf-8 -*-

#UNIVERSAL SETTINGS

import MySQLdb
#import re
#import subprocess
#from subprocess import call
#import os
#from datetime import datetime
#import json

txtdir = "/data/arxiv/pilot/texts/"

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
    for line in open(txtdir+"textids/totalcat"):
        fields = line.split()
        cursor.execute("LOAD DATA LOCAL INFILE '" +txtdir+"encoded/unigrams/"+fields[1]+".txt' INTO TABLE master_bookcounts CHARACTER SET utf8 (wordid,count) SET bookid="+fields[0]);  
    cursor.execute("ALTER TABLE master_bookcounts ENABLE KEYS")

def create_bigram_book_counts():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS master_bigrams (
        bookid MEDIUMINT NOT NULL, INDEX(bookid,word1,word2,count),
        word1 MEDIUMINT NOT NULL, INDEX (word1,word2,bookid,count),    
        word2 MEDIUMINT NOT NULL, INDEX(word2, word1, bookid, count),    
        count MEDIUMINT UNSIGNED NOT NULL);""")
    cursor.execute("ALTER TABLE master_bigrams DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    for line in open(txtdir+"textids/totalcat"):
        fields = line.split()
        cursor.execute("LOAD DATA LOCAL INFILE '" +txtdir+"encoded/bigrams/"+fields[1]+".txt' INTO TABLE master_bigrams (word1,word2,count) SET bookid="+fields[0]);  
    cursor.execute("ALTER TABLE master_bigrams ENABLE KEYS")

def load_book_list():
    print "Making a SQL table to hold the data"
    cursor.execute("""CREATE TABLE IF NOT EXISTS catalog (
        bookid MEDIUMINT, INDEX(bookid),
        date DATETIME,
        category VARCHAR(255)
        );""")
    cursor.execute("ALTER TABLE catalog DISABLE KEYS")
    print "loading data using LOAD DATA LOCAL INFILE"
    cursor.execute("""LOAD DATA LOCAL INFILE '"""
                   +txtdir+"""metadata.txt' 
                   INTO TABLE catalog
                   (bookid,date,category) """)
    cursor.execute("ALTER TABLE catalog ENABLE KEYS")

#load_word_list()
#create_unigram_book_counts()
#create_bigram_book_counts()
load_book_list()
