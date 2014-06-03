#!/usr/bin/python
# -*- coding: utf-8 -*-

import warnings
import json
import os
import decimal
import re
from MySQLdb import escape_string

def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, decimal.Decimal):
        obj = unicode(str(obj), encoding)
    return obj


def splitMySQLcode(string):
    """
    MySQL code can only be executed one command at a time, and fails if it has any empty slots
    So as a convenience wrapper, I'm just splitting it and returning an array.
    """
    try:
        output = ['%s;\n' % query for query in string.split(';') if re.search(r"\w", query)]
    except AttributeError:
        #Occurs when the field is completely empty
        output = []
    return output

class textids(dict):
    """
    This class is a dictionary that maps file-locations (which can be many characters long)
    to bookids (which are 3-byte integers).
    It's critically important to keep the already-existing data valid;
    so it doesn't overwrite the
    old stuff, instead it makes sure this python dictionary is always aligned with
    the text files on
    disk. As a result, additions to it always have to be made through the 'bump'
    method rather than
    ordinary assignment (since I, Ben, didn't know how to reset the default hash
    assignment to include
    this): and it has to be closed at the end to ensure the file is up-to-date at the end.

    Create a dictionary, and initialize it with all the bookids we already have.
    And make it so that any new entries are also written to disk, so that they are kept permanently.

    """

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


def guessBasedOnNameAndContents(metadataname,dictionary):
    """
    This makes a guess based on the data field's name and type.
    CUrrently it assumes everything is categorical; that can really chunk out on some text fields, but works much better for importing csvs. Probably we want to take some other things into account as well.
    """
    description = {"field":metadataname,"datatype":"categorical","type":"character","unique":True}

    example = dictionary.keys()[0]

    if type(example)==int:
        description["type"] = "integer"
    if type(example)==list:
        unique(example)==False

    if metadataname == "searchstring":
        return {"datatype": "searchstring", "field": "searchstring", "unique": True, "type": "text"}

    if re.search("date",metadataname) or re.search("time",metadataname):
        description["datatype"] = "time"

    values = [dictionary[key] for key in dictionary]
    averageNumberOfEntries = sum(values)/len(values)
    maxEntries = max(values)

#    print metadataname
#    print averageNumberOfEntries
#    print maxEntries
    if averageNumberOfEntries > 2:
        description["datatype"] = "categorical"

    return description



class dataField:
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

        for key in definition.iterkeys():
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
            self.outputloc = "files/metadata/%s.txt" % self.field

    def slowSQL(self, withIndex=False):
        """
        This returns something like "author VARCHAR(255)",
        a small definition string with an index, potentially.
        """
        mysqltypes = {
                      "character": "VARCHAR(255)",
                      "integer": "INT",
                      "text": "VARCHAR(5000)",
                      "decimal": "DECIMAL (9,4)"
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

        if withIndex and self.type != 'text':
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
            else:
                return None
        else:
            return None

    def buildDiskTable(self,fileLocation="default"):
        """
        Builds a disk table for a nonunique variable.
        """
        db = self.dbToPutIn
        dfield = self;

        if fileLocation == "default":
            fileLocation = "files/metadata/" + dfield.field + ".txt"

        print "Making a SQL table to hold the data for " + dfield.field

        q1 = """DROP TABLE IF EXISTS """       + dfield.field + "Disk"
        print "\n" + q1 + "\n"
        db.query(q1)
        db.query("""CREATE TABLE IF NOT EXISTS """ + dfield.field + """Disk (
        """ + self.anchor + " " +  self.anchorType + """,
        """ + dfield.slowSQL(withIndex=True) + """
        );""")
        db.query("ALTER TABLE " + dfield.field + "Disk DISABLE KEYS;")
        loadcode = """LOAD DATA LOCAL INFILE '""" + fileLocation +  """'
               INTO TABLE """ + dfield.field + """Disk
               FIELDS ESCAPED BY '';"""
        db.query(loadcode)
        #cursor = db.query("""SELECT count(*) FROM """ + dfield.field + """Disk""")
        #print "length is\n" + str(cursor.fetchall()[0][0]) + "\n\n\n"
        db.query("ALTER TABLE " + dfield.field + "Disk ENABLE KEYS")

    def buildIDTable(self):
        IDcode = self.buildIdTable()
        for query in splitMySQLcode(IDcode):
            self.dbToPutIn.query(query)
        
    def buildLookupTable(self):
        dfield = self;
        lookupCode = dfield.buildIdTable();
        lookupCode = lookupCode + dfield.fastSQLTable()
        for query in splitMySQLcode(lookupCode):
            dfield.dbToPutIn.query(query)

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
        if self.unique and self.anchor=="bookid":
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

        returnt += "CREATE TABLE tmp ENGINE=MYISAM SELECT  %(field)s,count(*) as count FROM  %(table)s GROUP BY  %(field)s;\n\n" % self.__dict__

        returnt += """CREATE TABLE IF NOT EXISTS %(field)s__id (
                      %(field)s__id %(intType)s PRIMARY KEY AUTO_INCREMENT,
                      %(field)s VARCHAR (255), INDEX (%(field)s), %(field)s__count MEDIUMINT);\n\n""" % self.__dict__
        returnt += """INSERT INTO %(field)s__id (%(field)s,%(field)s__count)
                      SELECT %(field)s,count FROM tmp LEFT JOIN %(field)s__id USING (%(field)s) WHERE %(field)s__id.%(field)s__id IS NULL
                      ORDER BY count DESC;\n\n""" % self.__dict__
        returnt += """DROP TABLE tmp;\n\n"""

        self.idCode = "%s__id" % self.field
        return returnt

    def updateVariableDescriptionTable(self):
        self.memoryCode = self.fastLookupTableIfNecessary()
        code = """INSERT IGNORE INTO masterVariableTable
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
            self.dbToPutIn.query("INSERT IGNORE INTO masterTableTable VALUES ('%s','%s','%s')" % (self.field+"heap",parentTab,escape_string(code)))
        if self.datatype=="categorical":
            #Variable Info
            code = """
            INSERT IGNORE INTO masterVariableTable
                    (dbname,     name,      type,       tablename,
                      anchor,      alias,     status,description)
           VALUES
                    ('%(field)s__id','%(field)s','lookup','%(fasttab)s',
                    '%(anchor)s','%(alias)s','hidden','') """ % self.__dict__
            self.dbToPutIn.query(code)
            #Separate Table Info
            code = self.fastLookupTableIfNecessary()
            #print code
            self.dbToPutIn.query("INSERT IGNORE INTO masterTableTable VALUES ('%s','%s','%s')" % (self.field+"Lookup",self.fasttab,escape_string(code)))

class variableSet:
    def __init__(self,
                originFile="files/metadata/jsoncatalog_derived.txt",
                anchorField="bookid",
                jsonDefinition=None,
                db=None):
        self.db = db
        self.dbname = db.dbname
        self.anchorField = anchorField
        self.originFile=originFile
        self.jsonDefinition=jsonDefinition
        if jsonDefinition==None:
            #Make a guess, why not?
            warnings.warn("""No field_descriptions file specified, so guessing based on variable names.
            Unintended consequences are possible""")
            self.jsonDefinition=self.guessAtFieldDescriptions()
        else:
            self.jsonDefinition = json.loads(open(jsonDefinition,"r").read())

        self.setTableNames()
        self.catalogLocation = "files/metadata/" + self.tableName + ".txt"


        self.variables = []
        for item in self.jsonDefinition:
            #The anchor field has special methods hard coded in.
            if item['field'] != self.anchorField:
                self.variables.append(dataField(item,self.db,anchor=anchorField,table=self.tableName,fasttab=self.fastName))

    def setTableNames(self):
        """
        For the base case, they're catalog and fastcat: otherwise, it's just they key
        and the first variable associated with it.
        """
        if self.originFile == "files/metadata/jsoncatalog_derived.txt":
            self.tableName = "catalog"
            self.fastName = "fastcat"
        else:
            try:
                self.tableName = self.jsonDefinition[0]['field'] + "_" + self.jsonDefinition[1]['field']
            except IndexError:
                #if it's only one element long, just name it after the variable itself.
                self.tableName = self.jsonDefinition[0]['field']
    
            self.fastName  = self.tableName + "heap"

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

    def uniques(self):
        return [variable for variable in self.variables if variable.unique]

    def notUniques(self):
        return [variable for variable in self.variables if not variable.unique]

    def anchorLookupDictionary(self):
        db = self.db
        anchor = self.anchorField
        self.fastAnchor = self.anchorField
        if anchor=="bookid" or anchor=="filename":
            self.fastAnchor = "bookid"
            bookids = textids()
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
                print anchor + "\n\n"
            self.fastAnchor=fastAnchor
            if fastAnchor != anchor:
                results = db.query("SELECT * FROM %sLookup;" % (anchor))
                for row in results.fetchall():
                    bookids[row[1]] = row[0]
                self.anchor=fastAnchor
                for variable in self.variables:
                    variable.anchor = fastAnchor
            else:
                #construct a phony dictionary that just returns what you gave
                bookids = selfDictionary()

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
        catalog = open(self.catalogLocation,'w')
        for variable in [variable for variable in variables if not variable.unique]:
            variable.output = open(variable.outputloc, 'w')

        for entry in metadatafile:
            try:
                #entry = to_unicode(entry)
                #entry = entry.replace('\\n', ' ')
                entry = json.loads(entry)
            except:
                warnings.warn("""WARNING: json parsing failed for this JSON line:
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n""" + entry)
                
                continue

            #We always lead with the bookid and the filename.
            #Unicode characters in filenames may cause problems?
            if self.anchorField=="bookid":
                self.anchorField="filename"

            filename = to_unicode(entry[self.anchorField])

            try:
                bookid = bookids[entry[self.anchorField]]
            except KeyError:
                if self.tableName=="catalog":
                    bookid = bookids.bump(entry[self.anchorField])
                else:
                    #If the key isn't in the name table, we have no use for this entry.
                    continue
            mainfields = [str(bookid),to_unicode(entry[self.anchorField])]
            if self.tableName != "catalog":
                #It can get problematic to have them both, so we're just writing over the
                #anchorField here.
                mainfields = [str(bookid)]
            #First, pull the unique variables and write them to the 'catalog' table
            for var in [variable for variable in variables if variable.unique]:
                if var.field not in [self.anchorField,self.fastAnchor]:
                    myfield = entry.get(var.field, "")
                    if myfield is None:
                        myfield = ''
                    mainfields.append(to_unicode(myfield))
            catalogtext = '%s\n' % '\t'.join(mainfields)
            catalog.write(catalogtext.encode('utf-8'))
            for variable in [variable for variable in variables if not variable.unique]:
                 #Each of these has a different file it must write to...
                outfile = variable.output
                lines = entry.get(variable.field, [])
                if isinstance(lines, basestring):
                    """
                    Allow a single element to be represented as a string
                    """
                    lines = [lines]
                if lines==None:
                    lines = []
                for line in lines:
                    try:
                        writing = '%s\t%s\n' % (str(bookid), line)
                        outfile.write(writing.encode('utf-8'))
                    except:
                        warnings.warn("some sort of error with bookid no. " +str(bookid) + ": " + json.dumps(lines))
                        pass
            if linenum > limit:
               break
            linenum=linenum+1
        for variable in [variable for variable in variables if not variable.unique]:
            variable.output.close()
        try:
            bookids.close()
        except AttributeError:
            #When it's a pure dictionary, not the weird textfile hybrid
            pass
        catalog.close()

    def loadMetadata(self):
        """
        Load in the metadata files which have already been created elsewhere.
        """

        #This function is called for the sideffect of assigning a `fastAnchor` field
        bookwormcodes = self.anchorLookupDictionary()
        db = self.db
        print "Making a SQL table to hold the catalog data"

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
                """ %self.tableName + ",\n".join(mysqlfields) + ") ENGINE=MYISAM;"
            db.query(createcode)
            #Never have keys before a LOAD DATA INFILE
            db.query("ALTER TABLE %s DISABLE KEYS" % self.tableName)
            print "loading data into %s using LOAD DATA LOCAL INFILE..." % self.tableName
            anchorFields = self.fastAnchor
            
            if self.tableName=="catalog":
                anchorFields = "bookid,filename"
                
            loadEntries = {
                "catLoc" : self.catalogLocation,
                "tabName" : self.tableName,
                "anchorFields" : anchorFields,
                "loadingFields" :  anchorFields+ "," + ','.join([field.field for field in self.variables if field.unique])
            }

            loadEntries['loadingFields'] = loadEntries['loadingFields'].rstrip(',')
            
            loadcode = """LOAD DATA LOCAL INFILE '%(catLoc)s'
                       INTO TABLE %(tabName)s FIELDS ESCAPED BY ''
                       (%(loadingFields)s)""" % loadEntries
            
            db.query(loadcode)
            print "enabling keys on %s" %self.tableName
            db.query("ALTER TABLE %s ENABLE KEYS" % self.tableName)

            #If there isn't a 'searchstring' field, it may need to be coerced in somewhere hereabouts

            #This here stores the number of words in between catalog updates, so that the full word counts only have to be done once since they're time consuming.
            if self.tableName=="catalog":
                self.createNwordsFile()

        for variable in self.notUniques():
            variable.buildDiskTable()

        for variable in self.variables:
            if variable.datatype=="categorical":
                variable.buildIDTable()

    def uniqueVariableFastSetup(self):
        fileCommand = """DROP TABLE IF EXISTS tmp;
        CREATE TABLE tmp
        (""" + self.fastAnchor + """ MEDIUMINT, PRIMARY KEY (""" + self.fastAnchor + """),
        """ +",\n".join([variable.fastSQL() for variable in self.variables if (variable.unique and variable.fastSQL() is not None)]) + """
        ) ENGINE=MEMORY;\n"""

        fileCommand += "INSERT INTO tmp SELECT " + self.fastAnchor + ", " + ",".join([variable.fastField for variable in self.variables if variable.unique and variable.fastSQL() is not None]) + " FROM %s " % self.tableName + " ".join([" JOIN %(field)s__id USING (%(field)s ) " % variable.__dict__ for variable in self.variables if variable.unique and variable.fastSQL() is not None and variable.datatype=="categorical"])+ ";\n"
        fileCommand += "DROP TABLE IF EXISTS %s;\n" % self.fastName
        fileCommand += "RENAME TABLE tmp TO %s;\n" % self.fastName        
        return fileCommand

    
    def updateMasterVariableTable(self):
        """
        All the categorical variables get a lookup table;
        we store the create code in the databse;
        """
        for variable in self.variables:
            variable.updateVariableDescriptionTable();

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
                    print("Unable to find a table to join the anchor (%s) against" % self.fastAnchor)
                    raise
            self.db.query("INSERT IGNORE INTO masterTableTable VALUES ('%s','%s','%s')" % (self.fastName,parentTab,escape_string(fileCommand)))
    
    def createNwordsFile(self):
        """
        A necessary supplement to the `catalog` table.
        """
        db = self.db

        db.query("CREATE TABLE IF NOT EXISTS nwords (bookid MEDIUMINT UNSIGNED, PRIMARY KEY (bookid), nwords INT);")
        db.query("UPDATE catalog JOIN nwords USING (bookid) SET catalog.nwords = nwords.nwords")
        db.query("INSERT INTO nwords (bookid,nwords) SELECT catalog.bookid,sum(count) FROM catalog LEFT JOIN nwords USING (bookid) JOIN master_bookcounts USING (bookid) WHERE nwords.bookid IS NULL GROUP BY catalog.bookid")
        db.query("UPDATE catalog JOIN nwords USING (bookid) SET catalog.nwords = nwords.nwords")


class selfDictionary():
    """
    Stupid little hack.
    Looks like a dictionary, but just returns itself.
    Used in cases where we don't actually need the dictionary.
    """
    def __init__(self):
        pass
    def __getitem__(self,string):
        return string
