#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import decimal
import re
from MySQLdb import escape_string
import logging
import subprocess
from .sqliteKV import KV

def to_unicode(obj):
    if isinstance(obj, bytes):
        obj = str(obj)
    if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, decimal.Decimal):
        obj = str(obj)
    return obj

def splitMySQLcode(string):
    
    """
    MySQL code can only be executed one command at a time, and fails if it has any empty slots
    So as a convenience wrapper, I'm just splitting it and returning an array.
    """
    try:
        output = ['%s;\n' % query for query in string.split(';') if re.search(r"\w", query)]
    except AttributeError:
        # Occurs when the field is completely empty
        output = []
    return output


def guessBasedOnNameAndContents(metadataname,dictionary):
    """
    This makes a guess based on the data field's name and type.
    CUrrently it assumes everything is categorical; that can really chunk out on some text fields, but works much better for importing csvs. Probably we want to take some other things into account as well.
    """
    description = {"field":metadataname,"datatype":"categorical","type":"character","unique":True}

    example = list(dictionary.keys())[0]

    if type(example) == int:
        description["type"] = "integer"

    if type(example) == list:
        description["unique"] = False

    if metadataname == "searchstring":
        return {"datatype": "searchstring", "field": "searchstring", "unique": True, "type": "text"}

    if re.search("date",metadataname) or re.search("time",metadataname):
        description["datatype"] = "time"

    values = [dictionary[key] for key in dictionary]
    averageNumberOfEntries = sum(values)/ len(values)

    if averageNumberOfEntries > 2:
        description["datatype"] = "categorical"

    return description


class dataField(object):
    """
    This define a class that supports a data field from a json definition.
    We'll use this to spit out appropriate sql code and JSON where needed.
    The 'definition' here means the user-generated array (submitted in json but
    parsed out before this) described in the Bookworm interface.
    This knows whether it's unique, whether it should treat itself as a date, etc.

    The complicated bits are about allowing fast lookups for arbitrary-length
    character lookups: for a variable like "country," it will also create
    the new field "country__id" and the table "countryLookup" to allow
    faster joins on the main database
    """

    def __init__(self, definition, dbToPutIn, anchorType="MEDIUMINT UNSIGNED", anchor="bookid",table="catalog",fasttab="fastcat"):
        #anchorType should be derived from somewhere.
        self.anchorType = anchorType
        self.anchor = anchor

        for key in definition.keys():
            vars(self)[key] = definition[key]
        self.dbToPutIn = dbToPutIn

        #ordinarily, a column has no alias other than itself.
        self.alias = self.field
        self.status = "hidden"

        #The table it's stored in will be either 'catalog', or a new
        #table named after the variable. For now, at least. (later the anchor should get used).

        self.fastField = self.field
        self.finalTable = fasttab
        if self.datatype == "categorical":
            self.type = "character"
            #This will catch a common sort of mistake (calling it text),
            #but also coerce any categorical data to have fewer than 255 characters.
            #This is worth it b/c a more than 255-character field will take *forever* to build.
            self.fastField = "%s__id" % self.field
            self.alias = self.fastField
            #If it's a categorical variable, it will be found in a lookup table.
            self.finalTable = self.field + "Lookup"
            self.status = "public"

        if self.datatype == "time":
            self.status = "public"

        if self.unique:
            self.table = table
            self.fasttab = fasttab

        else:
            self.table = self.field + "Disk"
            self.fasttab = self.field + "heap"
            self.outputloc = ".bookworm/metadata/%s.txt" % self.field


    def __repr__(self):
        val = "Data Field '{}'".format(self.field)
        val += "\n\tdatatype: {}".format(self.datatype)
        val += "\n\ttype: {}".format(self.type)        
        val += "\n\tuniqueness: {}".format(self.unique)            
        return val
    
    def slowSQL(self, withIndex=False):
        """
        This returns something like "author VARCHAR(255)",
        a small definition string with an index, potentially.
        """
        
        mysqltypes = {
            "character": "VARCHAR(255)",
            "integer": "INT",
            "text": "VARCHAR(5000)",
            "decimal": "DECIMAL (9,4)",
            "float": "FLOAT"
        }

        # Indexing both the field and against the anchor for fast memory table creation.
        indexstring = ", INDEX (%(field)s), INDEX (%(anchor)s, %(field)s " % self.__dict__
        #need to specify fixed prefix length on text strings: (http://dev.mysql.com/doc/refman/5.0/en/create-index.html)
        # If it's a text field, we need to curtail the index at 255 characters
        # or else indexes start timing out or eating up all the memory.
        indextypes = {
                      "character": "%s)" % indexstring,
                      "integer": "%s)" % indexstring,
                      "text": "%s (255) )" % indexstring,
                      "decimal": "%s)" % indexstring
                     }
        createstring = " %s %s" % (self.field, mysqltypes[self.type])

        if withIndex and self.type != 'text' and self.type != "float":
            return '%s%s' % (createstring, indextypes[self.type])

        return createstring

    def fastSQL(self):
        """
        This creates code to go in a memory table: it assumes that the disk
        tables are already there, and that a connection cursor is active.
        Memory tables in MySQL don't suppor the VARCHAR (they just take up all
        255 characters or whatever); thus, it has to be stored this other way.
        """
        if self.datatype != 'etc':
            if self.type == "character":
                self.setIntType()
                return " %(field)s__id %(intType)s" % self.__dict__
            if self.type == "integer":
                return " %s INT" % self.field
            if self.type == "decimal":
                return " %s DECIMAL (9,4) " % self.field
            if self.type == "float":
                return " %s FLOAT " % self.field
            else:
                return None
        else:
            return None

    def buildDiskTable(self,fileLocation="default"):
        """
        Builds a disk table for a nonunique variable.
        """
        db = self.dbToPutIn
        dfield = self

        if fileLocation == "default":
            fileLocation = ".bookworm/metadata/" + dfield.field + ".txt"

        logging.info("Making a SQL table to hold the data for " + dfield.field)

        q1 = """DROP TABLE IF EXISTS """ + dfield.field + "Disk"
        db.query(q1)
        db.query("""CREATE TABLE IF NOT EXISTS """ + dfield.field + """Disk (
        """ + self.anchor + " " + self.anchorType + """,
        """ + dfield.slowSQL(withIndex=True) + """
        );""")
        db.query("ALTER TABLE " + dfield.field + "Disk DISABLE KEYS;")
        loadcode = """LOAD DATA LOCAL INFILE '""" + fileLocation + """'
               INTO TABLE """ + dfield.field + """Disk
               FIELDS ESCAPED BY '';"""
        db.query(loadcode)
        # cursor = db.query("""SELECT count(*) FROM """ + dfield.field + """Disk""")
        db.query("ALTER TABLE " + dfield.field + "Disk ENABLE KEYS")

    def build_ID_and_lookup_tables(self):
        IDcode = self.buildIdTable()
        for query in splitMySQLcode(IDcode):
            self.dbToPutIn.query(query)
        for query in splitMySQLcode(self.fastLookupTableIfNecessary("MYISAM")):
            self.dbToPutIn.query(query)
        for query in splitMySQLcode(self.fastSQLTable("MYISAM")):
            self.dbToPutIn.query(query)

    def fastLookupTableIfNecessary(self, engine="MEMORY"):

        """
        This uses the already-created ID table to create a memory lookup.
        """
        self.engine = engine
        if self.datatype == 'categorical':
            logging.debug("Creating a memory lookup table for " + self.field)
            self.setIntType()
            self.maxlength = self.dbToPutIn.query("SELECT MAX(CHAR_LENGTH(%(field)s)) FROM %(field)s__id" % self.__dict__)
            self.maxlength = self.maxlength.fetchall()[0][0]
            self.maxlength = max([self.maxlength,1])
            code = """DROP TABLE IF EXISTS tmp;
                   CREATE TABLE tmp (%(field)s__id %(intType)s ,PRIMARY KEY (%(field)s__id),
                         %(field)s VARCHAR (%(maxlength)s) ) ENGINE=%(engine)s
                    SELECT %(field)s__id,%(field)s FROM %(field)s__id;""" % self.__dict__
            tname = self.field+"Lookup"
            if engine=="MYISAM":
                tname += "_"

            code += "DROP TABLE IF EXISTS {}; RENAME TABLE tmp to {}".format(tname,tname)
            return code
        return ""

    def fastSQLTable(self,engine="MEMORY"):
        #setting engine to another value will create these tables on disk.
        queries = ""
        self.engine = engine
        tname = self.field + "heap"
        if engine=="MYISAM":
            tname += "_"
        if self.unique and self.anchor=="bookid":
            pass #when it has to be part of a larger set
        if not self.unique and self.datatype == 'categorical':
            self.setIntType()
            queries += """DROP TABLE IF EXISTS tmp;"""
            queries += """CREATE TABLE tmp (%(anchor)s %(anchorType)s , INDEX (%(anchor)s),%(field)s__id %(intType)s ) ENGINE=%(engine)s; """ % self.__dict__
            if engine=="MYISAM":
                queries += "INSERT INTO tmp SELECT %(anchor)s ,%(field)s__id FROM %(field)s__id JOIN %(field)sDisk USING (%(field)s); " % self.__dict__
            elif engine=="MEMORY":
                queries += "INSERT INTO tmp SELECT * FROM {}_; ".format(tname)
            queries += "DROP TABLE IF EXISTS {}; RENAME TABLE tmp TO {}; ".format(tname,tname)
            
        if self.datatype == 'categorical' and self.unique:
            pass

        return queries

    def jsonDict(self):
        """
        DEPRECATED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #This builds a JSON dictionary that can be loaded into outside
        bookworm in the "options.json" file.
        It's a bad design decision; newer version
        just load this directly from the database.
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

    def buildIdTable(self, minimum_occurrence_rate = 1/100000):

        """
        This builds an integer crosswalk ID table with a field that stores categorical
        information in the fewest number of bytes. This is important because it can take
        significant amounts of time to group across categories if they are large:
        for example, with 4 million newspaper articles, on one server a GROUP BY with
        a 12-byte VARCHAR field takes 5.5 seconds, but a GROUP BY with a 3-byte MEDIUMINT
        field corresponding exactly to that takes 2.2 seconds on the exact same data.
        That sort of query is included in every single bookworm
        search multiple times, so it's necessary to optimize. 
        Plus, it means we can save space on memory storage
        in important ways as well.
        """
        #First, figure out how long the ID table has to be and make that into a datatype.
        #Joins and groups are slower the larger the field grouping on, so this is worth optimizing.
        self.setIntType()

        returnt = "DROP TABLE IF EXISTS tmp;\n\n"

        returnt += "CREATE TABLE tmp ENGINE=MYISAM SELECT  %(field)s,count(*) as count FROM %(table)s GROUP BY %(field)s;\n\n" % self.__dict__

        # XXXX to fix
        # Hardcoding this for now at one per 100K in the method definition. Could be user-set.
        n_documents = self.dbToPutIn.query("SELECT COUNT(*) FROM catalog").fetchall()[0][0]        
        self.minimum_count = round(n_documents*minimum_occurrence_rate)
        # XXXX            
        
        returnt +="DELETE FROM tmp WHERE count < %(minimum_count)s;" % self.__dict__

        returnt += "DROP TABLE IF EXISTS %(field)s__id;\n\n" % self.__dict__

        returnt += """CREATE TABLE IF NOT EXISTS %(field)s__id (
                      %(field)s__id %(intType)s PRIMARY KEY AUTO_INCREMENT,
                      %(field)s VARCHAR (255), INDEX (%(field)s, %(field)s__id), %(field)s__count MEDIUMINT UNSIGNED);\n\n""" % self.__dict__

        returnt += """INSERT INTO %(field)s__id (%(field)s,%(field)s__count)
                      SELECT %(field)s,count FROM tmp LEFT JOIN %(field)s__id USING (%(field)s) WHERE %(field)s__id.%(field)s__id IS NULL
                      ORDER BY count DESC;\n\n""" % self.__dict__

        returnt += """DROP TABLE tmp;\n\n"""

        self.idCode = "%s__id" % self.field
        return returnt

    def clear_associated_memory_tables(self):
        """
        Remove all data from memory tables associated with this variable.
        Useful when refreshing the database.
        """
        db = self.dbToPutIn
        def exists(tablename):
            return len(db.query("SHOW TABLES LIKE '" + tablename + "'").fetchall())>0
        if exists(self.fasttab):
            logging.debug("DELETING FROM " + self.fasttab)
            self.dbToPutIn.query("DELETE FROM " + self.fasttab)
        if not self.unique:
            if exists(self.field+"heap"):
                self.dbToPutIn.query("DELETE FROM " + self.field + "heap")
        if self.datatype=="categorical":
            if exists(self.field+"Lookup"):
                self.dbToPutIn.query("DELETE FROM " + self.field+"Lookup")
            
    def updateVariableDescriptionTable(self):
        self.memoryCode = self.fastLookupTableIfNecessary()
        code = """DELETE FROM masterVariableTable WHERE dbname="%(field)s";
        INSERT INTO masterVariableTable
        (dbname,     name,      type,       tablename,     anchor,      alias,     status,description)
           VALUES
        ('%(field)s','%(field)s','%(type)s','%(finalTable)s','%(anchor)s','%(alias)s','%(status)s','') """ % self.__dict__
        self.dbToPutIn.query(code)
        if not self.unique:
            code = self.fastSQLTable()
            try:
                parentTab = self.dbToPutIn.query("""
                SELECT tablename FROM masterVariableTable
                WHERE dbname='%s'""" % self.fastAnchor).fetchall()[0][0]
            except:
                parentTab="fastcat"
            self.dbToPutIn.query('DELETE FROM masterTableTable WHERE masterTableTable.tablename="%s";' % (self.field + "heap"))
            q = "INSERT INTO masterTableTable VALUES (%s,%s,%s)"
            self.dbToPutIn.query(q, (self.field + "heap", parentTab, code))
        if self.datatype=="categorical":
            #Variable Info
            
            code = """
            DELETE FROM masterVariableTable WHERE dbname='%(field)s__id';
            INSERT IGNORE INTO masterVariableTable
                    (dbname,     name,      type,       tablename,
                      anchor,      alias,     status,description)
            VALUES
                    ('%(field)s__id','%(field)s','lookup','%(fasttab)s',
                    '%(anchor)s','%(alias)s','hidden','') """ % self.__dict__
            self.dbToPutIn.query(code)
            #Separate Table Info
            code = self.fastLookupTableIfNecessary()
            self.dbToPutIn.query('DELETE FROM masterTableTable WHERE masterTableTable.tablename="%s";' %(self.field + "Lookup"))

#            code = escape_string(code)
#            if isinstance(code, bytes):
#                    code = str(code, 'utf-8')
#            if (code.startswith(b'b')):
#                print("\n\n")
#                print(code)

#            self.dbToPutIn.query(q)

            q = "INSERT INTO masterTableTable VALUES (%s, %s, %s)"
            
            self.dbToPutIn.query(q, (self.field+"Lookup", self.fasttab, code))
            

# Ugh! This could probably be solved just by putting a lot of
# backticks in the code!

mySQLreservedWords = set(["ACCESSIBLE", "ADD",
"ALL", "ALTER", "ANALYZE", "AND", "AS", "ASC", "ASENSITIVE", "BEFORE",
"BETWEEN", "BIGINT", "BINARY", "BLOB", "BOTH", "BY", "CALL",
"CASCADE", "CASE", "CHANGE", "CHAR", "CHARACTER", "CHECK", "COLLATE",
"COLUMN", "CONDITION", "CONSTRAINT", "CONTINUE", "CONVERT", "CREATE",
"CROSS", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
"CURRENT_USER", "CURSOR", "DATABASE", "DATABASES", "DAY_HOUR",
"DAY_MICROSECOND", "DAY_MINUTE", "DAY_SECOND", "DEC", "DECIMAL",
"DECLARE", "DEFAULT", "DELAYED", "DELETE", "DESC", "DESCRIBE",
"DETERMINISTIC", "DISTINCT", "DISTINCTROW", "DIV", "DOUBLE", "DROP",
"DUAL", "EACH", "ELSE", "ELSEIF", "ENCLOSED", "ESCAPED", "EXISTS",
"EXIT", "EXPLAIN", "FALSE", "FETCH", "FLOAT", "FLOAT4", "FLOAT8",
"FOR", "FORCE", "FOREIGN", "FROM", "FULLTEXT", "GENERAL", "GRANT",
"GROUP", "HAVING", "HIGH_PRIORITY", "HOUR_MICROSECOND", "HOUR_MINUTE",
"HOUR_SECOND", "IF", "IGNORE", "IGNORE_SERVER_IDS", "IN", "INDEX",
"INFILE", "INNER", "INOUT", "INSENSITIVE", "INSERT", "INT", "INT1",
"INT2", "INT3", "INT4", "INT8", "INTEGER", "INTERVAL", "INTO", "IS",
"ITERATE", "JOIN", "KEY", "KEYS", "KILL", "LEADING", "LEAVE", "LEFT",
"LIKE", "LIMIT", "LINEAR", "LINES", "LOAD", "LOCALTIME",
"LOCALTIMESTAMP", "LOCK", "LONG", "LONGBLOB", "LONGTEXT", "LOOP",
"LOW_PRIORITY", "MASTER_HEARTBEAT_PERIOD[c]",
"MASTER_SSL_VERIFY_SERVER_CERT", "MATCH", "MAXVALUE", "MEDIUMBLOB",
"MEDIUMINT", "MEDIUMTEXT", "MIDDLEINT", "MINUTE_MICROSECOND",
"MINUTE_SECOND", "MOD", "MODIFIES", "NATURAL", "NOT",
"NO_WRITE_TO_BINLOG", "NULL", "NUMERIC", "ON", "OPTIMIZE", "OPTION",
"OPTIONALLY", "OR", "ORDER", "OUT", "OUTER", "OUTFILE", "PRECISION",
"PRIMARY", "PROCEDURE", "PURGE", "RANGE", "READ", "READS",
"READ_WRITE", "REAL", "REFERENCES", "REGEXP", "RELEASE", "RENAME",
"REPEAT", "REPLACE", "REQUIRE", "RESIGNAL", "RESTRICT", "RETURN",
"REVOKE", "RIGHT", "RLIKE", "SCHEMA", "SCHEMAS", "SECOND_MICROSECOND",
"SELECT", "SENSITIVE", "SEPARATOR", "SET", "SHOW", "SIGNAL",
"SLOW[d]", "SMALLINT", "SPATIAL", "SPECIFIC", "SQL", "SQLEXCEPTION",
"SQLSTATE", "SQLWARNING", "SQL_BIG_RESULT", "SQL_CALC_FOUND_ROWS",
"SQL_SMALL_RESULT", "SSL", "STARTING", "STRAIGHT_JOIN", "TABLE",
"TERMINATED", "THEN", "TINYBLOB", "TINYINT", "TINYTEXT", "TO",
"TRAILING", "TRIGGER", "TRUE", "UNDO", "UNION", "UNIQUE", "UNLOCK",
"UNSIGNED", "UPDATE", "USAGE", "USE", "USING", "UTC_DATE", "UTC_TIME",
"UTC_TIMESTAMP", "VALUES", "VARBINARY", "VARCHAR", "VARCHARACTER",
"VARYING", "WHEN", "WHERE", "WHILE", "WITH", "WRITE", "XOR",
"YEAR_MONTH", "ZEROFILL", "WORDS", "NWORDS", "WORD", "UNIGRAM"])

class variableSet(object):
    def __init__(self,
                originFile=".bookworm/metadata/jsoncatalog_derived.txt",
                anchorField="bookid",
                jsonDefinition=None,
                db=None):
        self.db = db
        self.anchorField = anchorField
        self.originFile=originFile
        self.jsonDefinition=jsonDefinition
        logging.debug(jsonDefinition)
            
        if jsonDefinition==None:
            logging.warning("No field_descriptions.json file provided, so guessing based "
                            "on variable names. Unintended consequences are possible")
            self.jsonDefinition=self.guessAtFieldDescriptions()
        else:
            with open(jsonDefinition,"r") as fin:
                self.jsonDefinition = json.loads(fin.read())

        self.setTableNames()
        self.catalogLocation = ".bookworm/metadata/" + self.tableName + ".txt"


        self.variables = []

        for item in self.jsonDefinition:
            #The anchor field has special methods hard coded in.
            
            if item['field'] == self.anchorField:
                continue
            if item['field'].upper() in mySQLreservedWords:
                logging.warning(item['field'] + """ is a reserved word in MySQL, so can't be used as a Bookworm field name: skipping it for now, but you probably want to rename it to something different""")
                item['field'] = item['field'] + "___"
                continue
            self.variables.append(dataField(item,self.db,anchor=anchorField,table=self.tableName,fasttab=self.fastName))

    def __repr__(self):
        return "A variable set of {} objects".format(len(self.variables))
        
    def setTableNames(self):
        """
        For the base case, they're catalog and fastcat: otherwise, it's just they key
        and the first variable associated with it.
        """
        if os.path.split(self.originFile)[-1] == 'jsoncatalog_derived.txt':
            self.tableName = "catalog"
            self.fastName = "fastcat"
            
        else:
            try:
                self.tableName = self.jsonDefinition[0]['field'] + "_" + self.jsonDefinition[1]['field']
            except IndexError:
                #if it's only one element long, just name it after the variable itself.
                #Plus the string 'unique', to prevent problems of dual-named tables;
                self.tableName = "unick_" + self.jsonDefinition[0]['field']

            self.fastName = self.tableName + "heap"

    def guessAtFieldDescriptions(self,stopAfter=30000):
        allMyKeys = dict()
        i=1
        unique = True

        for line in open(self.originFile):
            i += 1
            entry = json.loads(line)
            for key in entry:
                if type(entry[key])==list:
                    unique=False
                else:
                    #Treat it for counting sake as a single element list.
                    entry[key] = [entry[key]]
                for value in entry[key]:
                    try:
                        allMyKeys[key][value] += 1
                    except KeyError:
                        try:
                            allMyKeys[key][value] = 1
                        except KeyError:
                            allMyKeys[key] = dict()
                            allMyKeys[key][value] = 1
            if i > stopAfter:
                break

        myOutput = []

        for metadata in allMyKeys:
            
            bestGuess = guessBasedOnNameAndContents(metadata,allMyKeys[metadata])
            if unique==False:
                bestGuess['unique'] = False
            
            myOutput.append(bestGuess)

        myOutput = [output for output in myOutput if output["field"] != "filename"]

        return myOutput

    def uniques(self,type="base"):
        """
        Some frequent patterns that tend to need to be iterated through.
        """

        if type=="base":
            return [variable for variable in self.variables if variable.unique]
        if type=="fast":
            return [variable for variable in self.variables if (variable.unique and variable.fastSQL() is not None)]
        if type=="categorical":
            return [variable for variable in self.variables if (variable.unique and variable.fastSQL() is not None and variable.datatype=="categorical")]
    
    def notUniques(self):
        return [variable for variable in self.variables if not variable.unique]

    def anchorLookupDictionary(self):
        db = self.db
        anchor = self.anchorField
        self.fastAnchor = self.anchorField
        
        if anchor == "bookid" and self.tableName != "catalog":
            self.fastAnchor="bookid"
            bookids = DummyDict()
            
        elif anchor=="filename" or anchor=="bookid":
            self.fastAnchor = "bookid"
            bookids = dict()
            try:
                """
                It is faster, better, and (on the first run only) sometimes necessary
                to pull the textids from the original files, not the database.
                """
                bookids = KV(".bookworm/metadata/textids.sqlite")
                for variable in self.variables:
                    variable.anchor=self.fastAnchor
            except IOError:
                logging.info("Pulling bookids from catalog...")
                results = db.query("SELECT bookid,filename FROM catalog;")
                logging.info("... bookids have been retrieved.")
                for row in results.fetchall():
                    bookids[row[1]] = row[0]
                logging.info("... and are loaded into a dictionary.")
                for variable in self.variables:
                    variable.anchor=self.fastAnchor
        else:
            query = """SELECT alias FROM masterVariableTable WHERE dbname='%s'""" % (anchor)
            bookids = dict()
            cursor = db.query("SELECT alias FROM masterVariableTable WHERE dbname = '%s'" % anchor)
            try:
                fastAnchor = cursor.fetchall()[0][0]
            except:
                if anchor in ["bookid","filename"]:
                    fastAnchor="bookid"
                logging.warning("Unable find an alias in the DB for anchor" + anchor + "\n\n")
            self.fastAnchor=fastAnchor
            if fastAnchor != anchor:
                results = db.query("SELECT * FROM %sLookup_;" % (anchor))
                for row in results.fetchall():
                    bookids[row[1]] = row[0]
                self.anchor=fastAnchor
                for variable in self.variables:
                    variable.anchor = fastAnchor
            else:
                #construct a phony dictionary that just returns what you gave
                bookids = DummyDict()

        return bookids

    def writeMetadata(self,limit=float("Inf")):
        #Write out all the metadata into files that MySQL is able to read in.
        """
        This is a general purpose, with a few special cases for the primary use case that this is the
        "catalog" table that hold the primary lookup information.
        """
        linenum = 1
        variables = self.variables
        bookids = self.anchorLookupDictionary()

        metadatafile = open(self.originFile)


        #Open files for writing to
        path = os.path.dirname(self.catalogLocation)
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise

        catalog = open(self.catalogLocation, 'w')

        for variable in [variable for variable in variables if not variable.unique]:
            variable.output = open(variable.outputloc, 'w')

        for entry in metadatafile:
            
            try:
                entry = json.loads(entry)
            except:
                logging.warning("""WARNING: json parsing failed for this JSON line:
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n""" + entry)
                
                continue

            #We always lead with the bookid and the filename.
            #Unicode characters in filenames may cause problems?
            if self.anchorField=="bookid" and self.tableName=="catalog":
                self.anchorField="filename"

            filename = to_unicode(entry[self.anchorField])

            try:
                bookid = bookids[entry[self.anchorField]]
            except KeyError:
                if self.tableName=="catalog":
                    logging.warning("No entry for {}".format(entry[self.anchorField]))
                    continue
                    # bookid = bookids.bump(entry[self.anchorField])
                else:
                    #If the key isn't in the name table, we have no use for this entry.
                    continue
            mainfields = [str(bookid),to_unicode(entry[self.anchorField])]
            
            if self.tableName != "catalog":
                #It can get problematic to have them both, so we're just writing over the
                #anchorField here.
                mainfields = [str(bookid)]
            # First, pull the unique variables and write them to the 'catalog' table
            
            for var in [variable for variable in variables if variable.unique]:
                if var.field not in [self.anchorField,self.fastAnchor]:
                    myfield = entry.get(var.field, "")
                    if myfield is None:
                        myfield = ''
                    mainfields.append(to_unicode(myfield))
            catalogtext = '%s\n' % '\t'.join(mainfields)
            try:
                catalog.write(catalogtext)
            except TypeError:
                catalog.write(catalogtext)
                
            for variable in [variable for variable in variables if not variable.unique]:
                # Each of these has a different file it must write to...
                outfile = variable.output
                lines = entry.get(variable.field, [])
                if isinstance(lines, (str, bytes, int)):
                    """
                    Allow a single element to be represented as a string
                    """
                    lines = [lines]
                if lines==None:
                    lines = []
                for line in lines:
                    try:
                        writing = '%s\t%s\n' % (str(bookid), to_unicode(line))
                        outfile.write(writing)
                    except:
                        logging.warning("some sort of error with bookid no. " +str(bookid) + ": " + json.dumps(lines))
                        pass
            if linenum > limit:
                break
            linenum=linenum+1
        for variable in [variable for variable in variables if not variable.unique]:
            variable.output.close()
        catalog.close()
        metadatafile.close()

    def loadMetadata(self):
        """
        Load in the metadata files which have already been created elsewhere.
        """

        #This function is called for the sideffect of assigning a `fastAnchor` field
        bookwormcodes = self.anchorLookupDictionary()
        db = self.db
        logging.info("Making a SQL table to hold the catalog data")

        if self.tableName=="catalog":
            """A few necessary basic fields"""
            mysqlfields = ["bookid MEDIUMINT UNSIGNED, PRIMARY KEY(bookid)", "filename VARCHAR(255)", "nwords INT"]
        else:
            mysqlfields = ["%s MEDIUMINT UNSIGNED, PRIMARY KEY (%s)" % (self.fastAnchor,self.fastAnchor)]
        for variable in self.uniques():
            createstring = variable.slowSQL(withIndex=True)
            mysqlfields.append(createstring)
        
        if len(mysqlfields) > 1:
            #This creates the main (slow) catalog table
            db.query("""DROP TABLE IF EXISTS %s """ % self.tableName)
            createcode = """CREATE TABLE IF NOT EXISTS %s (
                """ % self.tableName + ",\n".join(mysqlfields) + ") ENGINE=MYISAM;"
            try:
                db.query(createcode)
            except:
                logging.error("Unable to create table for metadata: SQL Code follows")
                logging.error(createcode)
                raise
            #Never have keys before a LOAD DATA INFILE
            db.query("ALTER TABLE %s DISABLE KEYS" % self.tableName)
            logging.info("loading data into %s using LOAD DATA LOCAL INFILE..." % self.tableName)
            anchorFields = self.fastAnchor
            
            if self.tableName=="catalog":
                anchorFields = "bookid,filename"
                
            loadEntries = {
                "catLoc": self.catalogLocation,
                "tabName": self.tableName,
                "anchorFields": anchorFields,
                "loadingFields": anchorFields + "," + ','.join([field.field for field in self.variables if field.unique])
            }

            loadEntries['loadingFields'] = loadEntries['loadingFields'].rstrip(',')
            logging.debug("loading in data from " + self.catalogLocation)
            loadcode = """LOAD DATA LOCAL INFILE '%(catLoc)s'
                       INTO TABLE %(tabName)s FIELDS ESCAPED BY ''
                       (%(loadingFields)s)""" % loadEntries
            
            db.query(loadcode)
            logging.info("enabling keys on %s" %self.tableName)
            db.query("ALTER TABLE %s ENABLE KEYS" % self.tableName)

            #If there isn't a 'searchstring' field, it may need to be coerced in somewhere hereabouts

            #This here stores the number of words in between catalog updates, so that the full word counts only have to be done once since they're time consuming.
            if self.tableName=="catalog":
                self.createNwordsFile()

        for variable in self.notUniques():
            variable.buildDiskTable()

        for variable in self.variables:
            if variable.datatype=="categorical":
                variable.build_ID_and_lookup_tables()
                
        if len(self.uniques()) > 0 and self.tableName!="catalog":
            #catalog has separate rules handled in CreateDatabase.py.
            fileCommand = self.uniqueVariableFastSetup("MYISAM")
            for query in splitMySQLcode(fileCommand):
                db.query(query)

    def uniqueVariableFastSetup(self,engine="MEMORY"):
        fileCommand = "DROP TABLE IF EXISTS tmp;"
        fileCommand += "CREATE TABLE tmp ({} MEDIUMINT UNSIGNED, PRIMARY KEY  ({}), ".format(
            self.fastAnchor,self.fastAnchor
            )
        fileCommand += ",\n".join([variable.fastSQL() for variable in self.variables if (variable.unique and variable.fastSQL() is not None)])
        fileCommand += ") ENGINE=%s;\n" % engine
        
        fast_fields = self.fastAnchor + ", " + ",".join([variable.fastField for variable in self.variables if variable.unique and variable.fastSQL() is not None])
        
        fileCommand += "INSERT INTO tmp SELECT " + fast_fields
        fileCommand += " FROM %s " % self.tableName
        fileCommand += " ".join([" JOIN %(field)s__id USING (%(field)s ) " % variable.__dict__ for variable in self.variables if variable.unique and variable.fastSQL() is not None and variable.datatype=="categorical"])+ ";\n"

        name = self.fastName
        if engine=="MYISAM":
            name += "_"
        fileCommand += "DROP TABLE IF EXISTS %s;\n" % name
        fileCommand += "RENAME TABLE tmp TO %s;\n" % name

        return fileCommand
    
    def updateMasterVariableTable(self):
        """
        All the categorical variables get a lookup table;
        we store the create code in the databse;
        """
        for variable in self.variables:
            # Make sure the variables know who their parent is
            variable.fastAnchor = self.fastAnchor
            # Update the referents for everything
            variable.updateVariableDescriptionTable()

        inCatalog = self.uniques()
        if len(inCatalog) > 0 and self.tableName!="catalog":
            #catalog has separate rules handled in CreateDatabase.py; so this builds
            #the big rectangular table otherwise.
            #It will fail if masterTableTable doesn't exister.
            fileCommand = self.uniqueVariableFastSetup()
            try:
                parentTab = self.db.query("""
                SELECT tablename FROM masterVariableTable
                WHERE dbname='%s'""" % self.fastAnchor).fetchall()[0][0]
            except:
                if self.fastAnchor=="bookid":
                    parentTab="fastcat"
                else:
                    logging.error("Unable to find a table to join the anchor (%s) against" % self.fastAnchor)
                    raise
            self.db.query('DELETE FROM masterTableTable WHERE masterTableTable.tablename="%s";' %self.fastName)
            self.db.query("INSERT INTO masterTableTable VALUES (%s, %s, %s)", (self.fastName,parentTab,escape_string(fileCommand)))
    
    def createNwordsFile(self):
        """
        A necessary supplement to the `catalog` table.
        """
        db = self.db

        db.query("CREATE TABLE IF NOT EXISTS nwords (bookid MEDIUMINT UNSIGNED, PRIMARY KEY (bookid), nwords INT);")
        db.query("UPDATE catalog JOIN nwords USING (bookid) SET catalog.nwords = nwords.nwords")
        db.query("INSERT INTO nwords (bookid,nwords) SELECT catalog.bookid,sum(count) FROM catalog LEFT JOIN nwords USING (bookid) JOIN master_bookcounts USING (bookid) WHERE nwords.bookid IS NULL GROUP BY catalog.bookid")
        db.query("UPDATE catalog JOIN nwords USING (bookid) SET catalog.nwords = nwords.nwords")



class DummyDict(dict):
    """
    Stupid little hack.
    Looks like a dictionary, but just returns itself.
    Used in cases where we don't actually need the dictionary.
    """
    # we need to have it there.
    def __missing__(self,key):
        return key        
