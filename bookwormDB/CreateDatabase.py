#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import MySQLdb
import re
import sys
import json
import os
from variableSet import dataField
from variableSet import variableSet
from variableSet import splitMySQLcode
import logging
import warnings
import anydbm



if logging.getLogger().isEnabledFor(logging.DEBUG):
    # Catch MYSQL warnings as errors if logging is set to debug.
    warnings.filterwarnings('error', category=MySQLdb.Warning) # For testing

warnings.filterwarnings('ignore', 'Table .* already exists')
warnings.filterwarnings("ignore", "Can't create database.*; database exists")
warnings.filterwarnings("ignore", "^Unknown table .*")
warnings.filterwarnings("ignore","Table 'mysql.table_stats' doesn't exist")


def text_id_dbm():
    """
    This quickly creates a key-value store for textids: storing on disk
    dramatically reduces memory consumption for bookworms of over 
    1 million documents.
    """
    dbm = anydbm.open(".bookworm/texts/textids.dbm","c")
    for file in os.listdir(".bookworm/texts/textids"):
        for line in open(".bookworm/texts/textids/" + file):
            line = line.rstrip("\n")
            splat = line.split("\t")
            try:
                dbm[splat[1]] = splat[0]
            except IndexError:
                if line=="":
                    # It's OK to have a blank line, let's say.
                    continue
                else:
                    raise
class DB:
    def __init__(self,dbname=None):
        from bookwormDB.configuration import Configfile
        try:
            configuration = Configfile("local")
            logging.debug("Connecting from the local config file")
        except IOError:
            try:
                configuration = Configfile("global")
                logging.debug("No bookworm.cnf in local file: connecting from global defaults")
            except IOError:
                configuration = Configfile("admin")
                logging.debug("No bookworm.cnf in local file: connecting from admin defaults")
                
        configuration.read_config_files()
        config = configuration.config
        if dbname==None:
            self.dbname = config.get("client","database")
        else:
            self.dbname = dbname
        self.username=config.get("client","user")
        self.password=config.get("client","password")
        self.conn = None
        
    def connect(self, setengine=True):
        #These scripts run as the Bookworm _Administrator_ on this machine; defined by the location of this my.cnf file.
        self.conn = MySQLdb.connect(read_default_file="~/.my.cnf",use_unicode='True', charset='utf8', db='', local_infile=1)
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS %s" % self.dbname)
        #Don't use native query attribute here to avoid infinite loops
        cursor.execute("SET NAMES 'utf8'")
        cursor.execute("SET CHARACTER SET 'utf8'")
        if setengine:
            try:
                cursor.execute("SET default_storage_engine=MYISAM")
            except:
                logging.error("Forcing default engine failed. On some versions of Mysql,\
                you may need to add \"default-storage-engine=MYISAM\" manually\
                to the [mysqld] user in /etc/my.cnf. Trying again to connect...")
                self.connect(setengine=False) 
        logging.debug("Connecting to %s" % self.dbname)
        cursor.execute("USE %s" % self.dbname)


    def query(self, sql):
        """
        Billy defined a separate query method here so that the common case of a connection being
        timed out doesn't cause the whole shebang to fall apart: instead, it just reboots
        the connection and starts up nicely again.
        """
        logging.debug(" -- Preparing to execute SQL code -- " + sql)
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except:
            try:
                self.connect()
                cursor = self.conn.cursor()
                cursor.execute(sql)
            except:
                logging.error("Query failed: \n" + sql + "\n")
                raise
        return cursor

class BookwormSQLDatabase:

    """
    This class gives interactions methods to a MySQL database storing Bookworm
    data. Although the primary methods are about loading data already created
    into the SQL database, it has a few other operations
    that write out text files needed by the API and the web front end:
    I take it as logical to do those here, since that how
    it fits chronologically in the bookworm-creation sequence.
    """

    def __init__(self,dbname=None,
                 variableFile=".bookworm/metadata/jsoncatalog_derived.txt"):
        """
        You can initialize it with a database name;
        otherwise it defaults to finding a
        Bookworm configuration file.

        It also may be initialized with a set of metadata.
        This is a little wonky, and may
        be deprecated in favor of a cleaner interface.
        """
        import bookwormDB.configuration
        self.config_manager = bookwormDB.configuration.Configfile("local")
        self.config_manager.read_config_files()
        config = self.config_manager.config
        if dbname==None:
            self.dbname = config.get("client","database")
        else:
            self.dbname = dbname
        self.conn = None

        self.db = DB(dbname=self.dbname)
        
        if variableFile is not None:
            self.setVariables(originFile=variableFile)

    def grantPrivileges(self):
        """
        Grants select-only privileges to a non-admin mysql user for the API to
        query with (safer).

        The Username for these privileges is pulled from the bookworm.cnf file.
        """
        import ConfigParser
        # This should be using the global configparser module, not the custom code here
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.read(["~/.my.cnf","/etc/my.cnf","/etc/mysql/my.cnf","bookworm.cnf"])
        username=config.get("client","user")
        password=config.get("client","password")
        self.db.query("GRANT SELECT ON %s.* TO '%s'@'localhost' IDENTIFIED BY '%s'" % (self.dbname,username,password))
    
    def setVariables(self,originFile,anchorField="bookid",
                     jsonDefinition=".bookworm/metadata/field_descriptions_derived.json"):
        self.variableSet = variableSet(originFile=originFile, anchorField=anchorField, jsonDefinition=jsonDefinition,db=self.db)

    def importNewFile(self,originFile,anchorField,jsonDefinition):
        """
        Add additional metadata from a source collection of json-formatted rows.
        originFile is the filename of the new metadata, in the same input format
        as the original jsoncatalog.txt
        anchorField is the field in the existing dataset it should be anchored onto;
        jsonDefinition is a filename pointing to a file
        of the format of field_descriptions.json describing the new data to ingest.
        If it is of type None, then one will be guessed at.
        """
        self.setVariables(originFile,anchorField=anchorField,jsonDefinition=jsonDefinition)
        self.variableSet.writeMetadata()
        self.load_book_list()
        self.variableSet.updateMasterVariableTable()
        for variable in self.variableSet.variables:
            variable.clear_associated_memory_tables()
        self.reloadMemoryTables()

    def create_database(self):
        dbname = self.dbname
        dbuser = self.dbuser
        dbpassword = self.dbpassword
        db = self.db
        #This must be run as a MySQL user with create_table privileges
        try:
            db.query("CREATE DATABASE " + dbname)
        except:
            logging.info("Database %s already exists: that might be intentional, so not dying" % dbname)

        "Setting up permissions for web user..."
        db.query("GRANT SELECT ON " + dbname + ".*" + " TO '" + dbuser + "'@'localhost' IDENTIFIED BY '" + dbpassword + "'")
        db.query("FLUSH PRIVILEGES")
        try:
            #a field to store stuff we might need later.
            db.query("CREATE TABLE IF NOT EXISTS bookworm_information (entry VARCHAR(255), PRIMARY KEY (entry), value VARCHAR(50000))")
        except:
            raise

    def load_word_list(self):
        db = self.db
        logging.info("Making a SQL table to hold the words")
        db.query("""DROP TABLE IF EXISTS words""")
        db.query("""CREATE TABLE IF NOT EXISTS words (
        wordid MEDIUMINT,
        word VARCHAR(255), INDEX (word),
        count BIGINT UNSIGNED,
        casesens VARBINARY(255),
        stem VARCHAR(255)
        );""")

        db.query("ALTER TABLE words DISABLE KEYS")
        logging.info("loading data using LOAD DATA LOCAL INFILE")
        db.query("""LOAD DATA LOCAL INFILE '.bookworm/texts/wordlist/wordlist.txt'
                   INTO TABLE words
                   CHARACTER SET binary
                   (wordid,word,count) """)
        logging.info("creating indexes on words table")
        db.query("ALTER TABLE words ENABLE KEYS")
        db.query("UPDATE words SET casesens=word")

    def load_book_list(self):
        """
        Loads in the tables that have already been created by a previous
        call to `Bookworm.variableSet.writeMetadata()`
        """
        self.variableSet.loadMetadata()

    def create_unigram_book_counts(self):
        db = self.db
        db.query("""DROP TABLE IF EXISTS master_bookcounts""")
        logging.info("Making a SQL table to hold the unigram counts")
        db.query("""CREATE TABLE master_bookcounts (
        bookid MEDIUMINT UNSIGNED NOT NULL, INDEX(bookid,wordid,count),
        wordid MEDIUMINT UNSIGNED NOT NULL, INDEX(wordid,bookid,count),
        count MEDIUMINT UNSIGNED NOT NULL);""")
        db.query("ALTER TABLE master_bookcounts DISABLE KEYS")
        logging.info("loading data using LOAD DATA LOCAL INFILE")
        for filename in os.listdir(".bookworm/texts/encoded/unigrams"):
            if not filename.endswith('.txt'):
                # Sometimes other files are in there; skip them.
                continue
            try:
                db.query("LOAD DATA LOCAL INFILE '.bookworm/texts/encoded/unigrams/"+filename+"' INTO TABLE master_bookcounts CHARACTER SET utf8 (bookid,wordid,count);")
            except:
                raise
        logging.info("Creating Unigram Indexes")
        db.query("ALTER TABLE master_bookcounts ENABLE KEYS")

    def create_bigram_book_counts(self):
        db = self.db
        logging.info("Making a SQL table to hold the bigram counts")
        db.query("""DROP TABLE IF EXISTS master_bigrams""")
        db.query("""CREATE TABLE master_bigrams (
        bookid MEDIUMINT UNSIGNED NOT NULL,
        word1 MEDIUMINT UNSIGNED NOT NULL, INDEX (word1,word2,bookid,count),
        word2 MEDIUMINT UNSIGNED NOT NULL,
        count MEDIUMINT UNSIGNED NOT NULL);""")
        db.query("ALTER TABLE master_bigrams DISABLE KEYS")
        logging.info("loading data using LOAD DATA LOCAL INFILE")
        for filename in os.listdir(".bookworm/texts/encoded/bigrams"):
            try:
                db.query("LOAD DATA LOCAL INFILE '.bookworm/texts/encoded/bigrams/"+filename+"' INTO TABLE master_bigrams CHARACTER SET utf8 (bookid,word1,word2,count);")
            except:
                raise
        logging.info("Creating bigram indexes")
        db.query("ALTER TABLE master_bigrams ENABLE KEYS")

    def loadVariableDescriptionsIntoDatabase(self):
        """
        This adds a description of files to the master variable table:
        also, crucially, it puts code specifying their fast creation there,
        where it will be executed on startup for all eternity.
        """
        db = self.db
        db.query("DROP TABLE IF EXISTS masterVariableTable")
        m = db.query("""
            CREATE TABLE IF NOT EXISTS masterVariableTable
              (dbname VARCHAR(255), PRIMARY KEY (dbname),
              name VARCHAR(255),
              type VARCHAR(255),
              tablename VARCHAR(255),
              anchor VARCHAR(255),
              alias VARCHAR(255),
              status VARCHAR(255),
              description VARCHAR(5000)
              ) ENGINE=MYISAM;
              """)
        tableTable = db.query("""
            CREATE TABLE IF NOT EXISTS masterTableTable
              (tablename VARCHAR(255), PRIMARY KEY (tablename),
              dependsOn VARCHAR(255),
              memoryCode VARCHAR(20000)) ENGINE=MYISAM;
              """)
        self.addFilesToMasterVariableTable()
        self.addWordsToMasterVariableTable()
        self.variableSet.updateMasterVariableTable()

    def reloadMemoryTables(self,force=False):
        """
        Checks to see if memory tables need to be repopulated (by seeing if they are empty)
        and then does so if necessary.
        """
        existingCreateCodes = self.db.query("SELECT tablename,memoryCode FROM masterTableTable").fetchall();
        for row in existingCreateCodes:
            """
            For each table, it checks to see if the table is currently populated; if not,
            it runs the stored code to repopulate the table. (It checks length because
            memory tables are emptied on a restart).
            """
            tablename = row[0]
            try:
                cursor = self.db.query("SELECT count(*) FROM %s" %(tablename))
                currentLength = cursor.fetchall()[0][0]
                logging.debug("Current Length is %d" %currentLength)
            except:
                currentLength = 0
            if currentLength==0 or force:
                for query in splitMySQLcode(row[1]):
                    self.db.query(query)

    def addFilesToMasterVariableTable(self):
        fastFieldsCreateList = ["bookid MEDIUMINT, PRIMARY KEY (bookid)","nwords MEDIUMINT"] +\
          [variable.fastSQL() for variable in self.variableSet.variables if (variable.unique and variable.fastSQL() is not None)]
        fileCommand = """DROP TABLE IF EXISTS tmp;
        CREATE TABLE tmp
        (""" +",\n".join(fastFieldsCreateList) + """
        ) ENGINE=MEMORY;"""
        #Also update the wordcounts for each text.
        fastFields = ["bookid","nwords"] + [variable.fastField for variable in self.variableSet.variables if variable.unique and variable.fastSQL() is not None]
        fileCommand += "INSERT INTO tmp SELECT " + ",".join(fastFields) + " FROM catalog " + " ".join([" JOIN %(field)s__id USING (%(field)s ) " % variable.__dict__ for variable in self.variableSet.variables if variable.unique and variable.fastSQL() is not None and variable.datatype=="categorical"])+ ";"
        fileCommand += "DROP TABLE IF EXISTS fastcat;"
        fileCommand += "RENAME TABLE tmp TO fastcat;"
        self.db.query('DELETE FROM masterTableTable WHERE masterTableTable.tablename="fastcat";')
        self.db.query("""INSERT IGNORE INTO masterTableTable VALUES
                   ('fastcat','fastcat','""" + fileCommand + """')""")

    def addWordsToMasterVariableTable(self):
        wordCommand = "DROP TABLE IF EXISTS tmp;"
        wordCommand += "CREATE TABLE tmp (wordid MEDIUMINT, PRIMARY KEY (wordid), word VARCHAR(30), INDEX (word), casesens VARBINARY(30),UNIQUE INDEX(casesens), lowercase CHAR(30), INDEX (lowercase) ) ENGINE=MEMORY;"
        wordCommand += "INSERT IGNORE INTO tmp SELECT wordid as wordid,word,casesens,LOWER(word) FROM words WHERE CHAR_LENGTH(word) <= 30 AND wordid <= 1500000 ORDER BY wordid;"
        wordCommand += "DROP TABLE IF EXISTS wordsheap;"
        wordCommand += "RENAME TABLE tmp TO wordsheap;"
        query = """INSERT IGNORE INTO masterTableTable
                   VALUES ('wordsheap','wordsheap','""" + MySQLdb.escape_string(wordCommand) + """')"""
        logging.info("Creating wordsheap")
        self.db.query(query)
        
    def jsonify_data(self):
        variables = self.variableSet.variables
        dbname = self.dbname
        #This creates a JSON file compliant with the Bookworm web site.
        #Deprecated.
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
            logging.warning("WARNING: Not enough info for a default search (like, no time variable maybe?)--likely to be some big problems with your bookworm.")
        output['ui_components'] = ui_components
        outfile = open('.bookworm/%s.json' % dbname, 'w')
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
                    "read_default_file": "/etc/mysql/my.cnf",
                   }
        addCode = json.dumps(api_info)
        logging.info(addCode)
        db.query("INSERT INTO API_settings VALUES ('%s');" % addCode)

    def update_Porter_stemming(self): #We use stems occasionally.
        """
        Still not executed.
        """
        logging.info("Updating stems from Porter algorithm...")
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

