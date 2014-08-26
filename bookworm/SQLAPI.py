#!/usr/local/bin/python

import sys
import json
import cgi
import re
import numpy #used for smoothing.
import copy
import decimal
import MySQLdb
import warnings
import hashlib

"""
#There are 'fast' and 'full' tables for books and words;
#that's so memory tables can be used in certain cases for fast, hashed matching, but longer form data (like book titles)
can be stored on disk. Different queries use different types of calls.
#Also, certain metadata fields are stored separately from the main catalog table;
"""

from knownHosts import *

class dbConnect(object):
    #This is a read-only account
    def __init__(self,prefs):
        self.dbname = prefs['database']
        self.db = MySQLdb.connect(host=prefs['HOST'],read_default_file = prefs['read_default_file'],use_unicode='True',charset='utf8',db=prefs['database'])
        self.cursor = self.db.cursor()

# The basic object here is a 'userquery:' it takes dictionary as input, as defined in the API, and returns a value
# via the 'execute' function whose behavior
# depends on the mode that is passed to it.
# Given the dictionary, it can return a number of objects.
# The "Search_limits" array in the passed dictionary determines how many elements it returns; this lets multiple queries be bundled together.
# Most functions describe a subquery that might be combined into one big query in various ways.

class userqueries:
    #This is a set of userqueries that are bound together; each element in search limits is iterated over, and we're done.
    #currently used for various different groups sent in a bundle (multiple lines on a Bookworm chart).
    #A sufficiently sophisticated 'group by' search might make this unnecessary.
    #But until that day, it's useful to be able to return lists of elements, which happens in here.

    def __init__(self,outside_dictionary = {"counttype":["Percentage_of_Books"],"search_limits":[{"word":["polka dot"],"LCSH":["Fiction"]}]},db = None):
        try:
            self.database = outside_dictionary.setdefault('database', 'default')
            prefs = general_prefs[self.database]
        except KeyError: #If it's not in the option, use some default preferences and search on localhost. This will work in most cases here on out.
            prefs = general_prefs['default']
            prefs['database'] = self.database
        self.prefs = prefs

        self.wordsheap = prefs['fastword']
        self.words = prefs['fullword']
        if 'search_limits' not in outside_dictionary.keys():
            outside_dictionary['search_limits'] = [{}]
        #coerce one-element dictionaries to an array.
        if isinstance(outside_dictionary['search_limits'],dict):
            #(allowing passing of just single dictionaries instead of arrays)
            outside_dictionary['search_limits'] = [outside_dictionary['search_limits']]
        self.returnval = []
        self.queryInstances = []
        db = dbConnect(prefs)
        databaseScheme = databaseSchema(db)
        for limits in outside_dictionary['search_limits']:
            mylimits = copy.deepcopy(outside_dictionary)
            mylimits['search_limits'] = limits
            localQuery = userquery(mylimits,db=db,databaseScheme=databaseScheme)
            self.queryInstances.append(localQuery)
            self.returnval.append(localQuery.execute())

    def execute(self):
        
        return self.returnval


class userquery:
    def __init__(self,outside_dictionary = {"counttype":["Percentage_of_Books"],"search_limits":{"word":["polka dot"],"LCSH":["Fiction"]}},db=None,databaseScheme=None):
        #Certain constructions require a DB connection already available, so we just start it here, or use the one passed to it.
        try:
            self.prefs = general_prefs[outside_dictionary['database']]
        except KeyError:
            #If it's not in the option, use some default preferences and search on localhost. This will work in most cases here on out.
            self.prefs = general_prefs['default']
            self.prefs['database'] = outside_dictionary['database']
        self.outside_dictionary = outside_dictionary
        #self.prefs = general_prefs[outside_dictionary.setdefault('database','presidio')]
        self.db = db
        if db is None:
            self.db = dbConnect(self.prefs)
        self.databaseScheme = databaseScheme
        if databaseScheme is None:
            self.databaseScheme = databaseSchema(self.db)

        self.cursor = self.db.cursor
        self.wordsheap = self.prefs['fastword']
        self.words = self.prefs['fullword']
        """
        I'm now allowing 'search_limits' to either be a dictionary or an array of dictionaries:
        this makes the syntax cleaner on most queries,
        while still allowing some long ones from the Bookworm website.
        """
        try:
            if isinstance(outside_dictionary['search_limits'],list):
                outside_dictionary['search_limits'] = outside_dictionary['search_limits'][0]
        except:
            outside_dictionary['search_limits'] = dict()
        #outside_dictionary = self.limitCategoricalQueries(outside_dictionary)
        self.defaults(outside_dictionary) #Take some defaults
        self.derive_variables() #Derive some useful variables that the query will use.

    def defaults(self,outside_dictionary):
        #these are default values;these are the only values that can be set in the query
        #search_limits is an array of dictionaries;
        #each one contains a set of limits that are mutually independent
        #The other limitations are universal for all the search limits being set.

        #Set up a dictionary for the denominator of any fraction if it doesn't already exist:
        self.search_limits = outside_dictionary.setdefault('search_limits',[{"word":["polka dot"]}])
        self.words_collation = outside_dictionary.setdefault('words_collation',"Case_Insensitive")

        lookups = {"Case_Insensitive":'word','lowercase':'lowercase','casesens':'casesens',"case_insensitive":"word","Case_Sensitive":"casesens","All_Words_with_Same_Stem":"stem",'stem':'stem'}
        self.word_field = lookups[self.words_collation]

        self.time_limits = outside_dictionary.setdefault('time_limits',[0,10000000])
        self.time_measure = outside_dictionary.setdefault('time_measure','year')

        self.groups = set()
        self.outerGroups = [] #[] #Only used on the final join; directionality matters, unlike for the other ones.
        self.finalMergeTables=set()
        try:
            groups = outside_dictionary['groups']
        except:
            groups = [outside_dictionary['time_measure']]

        if groups == [] or groups == ["unigram"]:
            #Set an arbitrary column name that will always be true if nothing else is set.
            groups.insert(0,"1 as In_Library")

        if (len (groups) > 1):
            pass
            #self.groups = credentialCheckandClean(self.groups)
            #Define some sort of limitations here, if not done in dbbindings.py

        for group in groups:

            #There's a special set of rules for how to handle unigram and bigrams
            multigramSearch = re.match("(unigram|bigram|trigram)(\d)?",group)

            if multigramSearch:
                if group=="unigram":
                    gramPos = "1"
                    gramType = "unigram"

                else:
                    gramType = multigramSearch.groups()[0]
                    try:
                        gramPos = multigramSearch.groups()[1]
                    except:
                        print "currently you must specify which bigram element you want (eg, 'bigram1')"
                        raise

                lookupTableName = "%sLookup%s" %(gramType,gramPos)
                self.outerGroups.append("%s.%s as %s" %(lookupTableName,self.word_field,group))
                self.finalMergeTables.add(" JOIN wordsheap as %s ON %s.wordid=w%s" %(lookupTableName,lookupTableName,gramPos))
                self.groups.add("words%s.wordid as w%s" %(gramPos,gramPos))

            else:
                self.outerGroups.append(group)
                try:
                    if self.databaseScheme.aliases[group] != group:
                        #Search on the ID field, not the basic field.
                        #debug(self.databaseScheme.aliases.keys())
                        self.groups.add(self.databaseScheme.aliases[group])
                        table = self.databaseScheme.tableToLookIn[group]

                        joinfield = self.databaseScheme.aliases[group]
                        self.finalMergeTables.add(" JOIN " + table + " USING (" + joinfield + ") ")
                    else:
                        self.groups.add(group)
                except KeyError:
                    self.groups.add(group)                

        """
        There are the selections which can include table refs, and the groupings, which may not:
        and the final suffix to enable fast lookup
        """

        self.selections = ",".join(self.groups)
        self.groupings  = ",".join([re.sub(".* as","",group) for group in self.groups])

        self.joinSuffix = "" + " ".join(self.finalMergeTables)

        """
        Define the comparison set if a comparison is being done.
        """
        #Deprecated--tagged for deletion
        #self.determineOutsideDictionary()

        #This is a little tricky behavior here--hopefully it works in all cases. It drops out word groupings.

        self.counttype = outside_dictionary.setdefault('counttype',["WordCount"])

        if isinstance(self.counttype,basestring):
            self.counttype = [self.counttype]

        #index is deprecated,but the old version uses it.
        self.index  = outside_dictionary.setdefault('index',0)
        """
        #Ordinarily, the input should be an an array of groups that will both select and group by.
        #The joins may be screwed up by certain names that exist in multiple tables, so there's an option to do something like
        #SELECT catalog.bookid as myid, because WHERE clauses on myid will work but GROUP BY clauses on catalog.bookid may not
        #after a sufficiently large number of subqueries.
        #This smoothing code really ought to go somewhere else, since it doesn't quite fit into the whole API mentality and is
        #more about the webpage. It is only included here as a stopgap: NO FURTHER APPLICATIONS USING IT SHOULD BE BUILT.
        """

        self.smoothingType = outside_dictionary.setdefault('smoothingType',"triangle")
        self.smoothingSpan = outside_dictionary.setdefault('smoothingSpan',3)
        self.method = outside_dictionary.setdefault('method',"Nothing")

    def determineOutsideDictionary(self):
        """
        deprecated--tagged for deletion.
        """
        self.compare_dictionary = copy.deepcopy(self.outside_dictionary)
        if 'compare_limits' in self.outside_dictionary.keys():
            self.compare_dictionary['search_limits'] = self.outside_dictionary['compare_limits']
            del self.outside_dictionary['compare_limits']
        elif sum([bool(re.search(r'\*',string)) for string in self.outside_dictionary['search_limits'].keys()]) > 0:
            #If any keys have stars at the end, drop them from the compare set
            #This is often a _very_ helpful definition for succinct comparison queries of many types.
            #The cost is that an asterisk doesn't allow you

            for key in self.outside_dictionary['search_limits'].keys():
                if re.search(r'\*',key):
                    #rename the main one to not have a star
                    self.outside_dictionary['search_limits'][re.sub(r'\*','',key)] = self.outside_dictionary['search_limits'][key]
                    #drop it from the compare_limits and delete the version in the search_limits with a star
                    del self.outside_dictionary['search_limits'][key]
                    del self.compare_dictionary['search_limits'][key]
        else: #if nothing specified, we compare the word to the corpus.
            deleted = False
            for key in self.outside_dictionary['search_limits'].keys():
                if re.search('words?\d',key) or re.search('gram$',key) or re.match(r'word',key):
                    del self.compare_dictionary['search_limits'][key]
                    deleted = True
            if not deleted:
                #If there are no words keys, just delete the first key of any type.
                #Sort order can't be assumed, but this is a useful failure mechanism of last resort. Maybe.
                try:
                    del self.compare_dictionary['search_limits'][self.outside_dictionary['search_limits'].keys()[0]]
                except:
                    pass
        """
        The grouping behavior here is not desirable, but I'm not quite sure how yet.
        Aha--one way is that it accidentally drops out a bunch of options. I'm just disabling it: let's see what goes wrong now.
        """
        try:
            pass#self.compare_dictionary['groups'] = [group for group in self.compare_dictionary['groups'] if not re.match('word',group) and not re.match("[u]?[bn]igram",group)]# topicfix? and not re.match("topic",group)]
        except:
            self.compare_dictionary['groups'] = [self.compare_dictionary['time_measure']]


    def derive_variables(self):
        #These are locally useful, and depend on the search limits put in.
        self.limits = self.search_limits
        #Treat empty constraints as nothing at all, not as full restrictions.
        for key in self.limits.keys():
            if self.limits[key] == []:
                del self.limits[key]
        self.set_operations()
        self.create_catalog_table()
        self.make_catwhere()
        self.make_wordwheres()

    def tablesNeededForQuery(self,fieldNames=[]):
        db = self.db
        neededTables = set()
        tablenames = dict()
        tableDepends = dict()
        db.cursor.execute("SELECT dbname,alias,tablename,dependsOn FROM masterVariableTable JOIN masterTableTable USING (tablename);")
        for row in db.cursor.fetchall():
            tablenames[row[0]] = row[2]
            tableDepends[row[2]] = row[3]

        for fieldname in fieldNames:
            parent = ""
            try:
                current = tablenames[fieldname]
                neededTables.add(current)
                n = 1
                while parent not in ['fastcat','wordsheap']:
                    parent = tableDepends[current]
                    neededTables.add(parent)
                    current = parent;
                    n+=1
                    if n > 100:
                        raise TypeError("Unable to handle this; seems like a recursion loop in the table definitions.")
                    #This will add 'fastcat' or 'wordsheap' exactly once per entry
            except KeyError:
                pass
            
        return neededTables

    def create_catalog_table(self):
        self.catalog = self.prefs['fastcat'] #'catalog' #Can be replaced with a more complicated query in the event of longer joins.

        """
        This should check query constraints against a list of tables, and join to them.
        So if you query with a limit on LCSH, and LCSH is listed as being in a separate table,
        it joins the table "LCSH" to catalog; and then that table has one column, ALSO
        called "LCSH", which is matched against. This allows a bookid to be a member of multiple catalogs.
        """

        #for limitation in self.prefs['separateDataTables']:
        #    #That re.sub thing is in here because sometimes I do queries that involve renaming.
        #    if limitation in [re.sub(" .*","",key) for key in self.limits.keys()] or limitation in [re.sub(" .*","",group) for group in self.groups]:
        #        self.catalog = self.catalog + """ JOIN """ + limitation + """ USING (bookid)"""

        """
        Here it just pulls every variable and where to look for it.
        """


        self.relevantTables = set()

        databaseScheme = self.databaseScheme
        columns = []
        for columnInQuery in [re.sub(" .*","",key) for key in self.limits.keys()] + [re.sub(" .*","",group) for group in self.groups]:
            columns.append(columnInQuery)
            try:
                self.relevantTables.add(databaseScheme.tableToLookIn[columnInQuery])
                try:
                    self.relevantTables.add(databaseScheme.tableToLookIn[databaseScheme.anchorFields[columnInQuery]])
                    try:
                        self.relevantTables.add(databaseScheme.tableToLookIn[databaseScheme.anchorFields[databaseScheme.anchorFields[columnInQuery]]])
                    except KeyError:
                        pass
                except KeyError:
                    pass
            except KeyError:
                pass
                #Could raise as well--shouldn't be errors--but this helps back-compatability.

#        if "catalog" in self.relevantTables and self.method != "bibliography_query":
#            self.relevantTables.remove('catalog')
        try:
            moreTables = self.tablesNeededForQuery(columns)
        except MySQLdb.ProgrammingError:
            #What happens on old-style Bookworm constructions.
            moreTables = set()
        self.relevantTables = self.relevantTables.union(moreTables)
        self.catalog = "fastcat"
        for table in self.relevantTables:
            if table!="fastcat" and table!="words" and table!="wordsheap" and table!="master_bookcounts" and table!="master_bigrams":
                self.catalog = self.catalog + """ NATURAL JOIN """ + table + " "

    def make_catwhere(self):
        #Where terms that don't include the words table join. Kept separate so that we can have subqueries only working on one half of the stack.
        catlimits = dict()
        for key in self.limits.keys():
            ###Warning--none of these phrases can be used ina  bookworm as a custom table names.
            if key not in ('word','word1','word2','hasword') and not re.search("words\d",key):
                catlimits[key] = self.limits[key]
        if len(catlimits.keys()) > 0:
            self.catwhere = where_from_hash(catlimits)
        else:
            self.catwhere = "TRUE"
        if 'hasword' in self.limits.keys():
            """
            Because derived tables don't carry indexes, we're just making the new tables
            with indexes on the fly to be stored in a temporary database, "bookworm_scratch"
            Each time a hasword query is performed, the results of that query are permanently cached;
            they're stored as a table that can be used in the future.

            This will create problems if database contents are changed; there needs to be some mechanism for 
            clearing out the cache periodically.
            """

            if self.limits['hasword'] == []:
                del self.limits['hasword']
                return

            #deepcopy lets us get a real copy of the dictionary
            #that can be changed without affecting the old one.
            mydict = copy.deepcopy(self.outside_dictionary)
            # This may make it take longer than it should; we might want the list to
            # just be every bookid with the given word rather than
            # filtering by the limits as well.
            # It's not obvious to me which will be faster.
            mydict['search_limits'] = copy.deepcopy(self.limits)
            if isinstance(mydict['search_limits']['hasword'],basestring):
                #Make sure it's an array
                mydict['search_limits']['hasword'] =  [mydict['search_limits']['hasword']] 
            """
            #Ideally, this would shuffle into an order ensuring that the
            rarest words were nested deepest.
            #That would speed up query execution by ensuring there
            wasn't some massive search for 'the' being
            #done at the end.

            Instead, it just pops off the last element and sets up a
            recursive nested join. for every element in the 
            array.
            """
            mydict['search_limits']['word'] = [mydict['search_limits']['hasword'].pop()]
            if len(mydict['search_limits']['hasword'])==0:
                del mydict['search_limits']['hasword']
            tempquery = userquery(mydict,databaseScheme=self.databaseScheme)
            listofBookids = tempquery.bookid_query()

            #Unique identifier for the query that persists across the 
            #various subqueries.
            queryID  = hashlib.sha1(listofBookids).hexdigest()[:20]

            tmpcatalog = "bookworm_scratch.tmp" + re.sub("-","",queryID)

            try:
                self.cursor.execute("CREATE TABLE %s (bookid MEDIUMINT, PRIMARY KEY (bookid)) ENGINE=MYISAM;" %tmpcatalog)
                self.cursor.execute("INSERT IGNORE INTO %s %s;" %(tmpcatalog,listofBookids))

            except MySQLdb.OperationalError,e:
                #Usually the error will be 1050, which is a good thing: it means we don't need to
                #create the table.
                #If it's not, something bad is happening.
                if not re.search("1050.*already exists",str(e)):
                    raise
            self.catalog += " NATURAL JOIN %s "%(tmpcatalog)


    def make_wordwheres(self):
        self.wordswhere = " TRUE "
        self.max_word_length = 0
        limits = []
        """
        "unigram" or "bigram" can be used as an alias for "word" in the search_limits field.
        """

        for gramterm in ['unigram','bigram']:
            if gramterm in self.limits.keys() and not "word" in self.limits.keys():
                self.limits['word'] = self.limits[gramterm]
                del self.limits[gramterm]

        if 'word' in self.limits.keys():
            """
            This doesn't currently allow mixing of one and two word searches together in a logical way.
            It might be possible to just join on both the tables in MySQL--I'm not completely sure what would happen.
            But the philosophy has been to keep users from doing those searches as far as possible in any case.
            """
            for phrase in self.limits['word']:
                locallimits = dict()
                array = phrase.split(" ")
                n = 0
                for word in array:
                    n += 1
                    searchingFor = word
                    if self.word_field=="stem":
                        from nltk import PorterStemmer
                        searchingFor = PorterStemmer().stem_word(searchingFor)
                    if self.word_field=="case_insensitive" or self.word_field=="Case_Insensitive":
                        searchingFor = searchingFor.lower()

                    selectString =  "SELECT wordid FROM wordsheap WHERE %s = '%s'" %(self.word_field,searchingFor)
                    cursor = self.db.cursor;
                    cursor.execute(selectString)
                    for row in cursor.fetchall():
                        wordid = row[0]
                        try:
                            locallimits['words'+str(n) + ".wordid"] += [wordid]
                        except KeyError:
                            locallimits['words'+str(n) + ".wordid"] = [wordid]
                    self.max_word_length = max(self.max_word_length,n)

                #Strings have already been escaped, so don't need to be escaped again.
                if len(locallimits.keys()) > 0:
                    limits.append(where_from_hash(locallimits,comp = " = ",escapeStrings=False))
                #XXX for backward compatability
                self.words_searched = phrase
                #XXX end deprecated block
            self.wordswhere = "(" + ' OR '.join(limits) + ")"
            if limits == []:
                #In the case that nothing has been found, tell it explicitly to search for
                #a condition when nothing will be found.
                self.wordswhere = "words1.wordid=-1"


        wordlimits = dict()

        limitlist = copy.deepcopy(self.limits.keys())

        for key in limitlist:
            if re.search("words\d",key):
                wordlimits[key] = self.limits[key]
                self.max_word_length = max(self.max_word_length,2)
                del self.limits[key]

        if len(wordlimits.keys()) > 0:
            self.wordswhere = where_from_hash(wordlimits)

        return self.wordswhere

    def build_wordstables(self):
        #Deduce the words tables we're joining against. The iterating on this can be made more general to get 3 or four grams in pretty easily.
        #This relies on a determination already having been made about whether this is a unigram or bigram search; that's reflected in the keys passed.

        if (self.max_word_length == 2 or re.search("words2",self.selections)):

            self.maintable = 'master_bigrams'

            self.main = '''
                 JOIN
                 master_bigrams as main
                 ON ('''+ self.prefs['fastcat'] +'''.bookid=main.bookid)
                 '''

            self.wordstables =  """
            JOIN %(wordsheap)s as words1 ON (main.word1 = words1.wordid)
            JOIN %(wordsheap)s as words2 ON (main.word2 = words2.wordid) """ % self.__dict__

        #I use a regex here to do a blanket search for any sort of word limitations. That has some messy sideffects (make sure the 'hasword'
        #key has already been eliminated, for example!) but generally works.

        elif self.max_word_length == 1 or re.search("[^h][^a][^s]word",self.selections) or re.search("topic",self.selections):
            self.maintable = 'master_bookcounts'
            self.main = '''
                NATURAL JOIN
                 master_bookcounts as main '''
                 #ON (''' + self.prefs['fastcat'] + '''.bookid=main.bookid)'''
            self.wordstables = """
              JOIN ( %(wordsheap)s as words1)  ON (main.wordid = words1.wordid)
             """ % self.__dict__

        else:
            """
            Have _no_ words table if no words searched for or grouped by;
            instead just use nwords. This
            means that we can use the same basic functions both to build the
            counts for word searches and
            for metadata searches, which is valuable because there is a
            metadata-only search built in to every single ratio
            query. (To get the denominator values).
            """
            self.main = " "
            self.operation = ','.join(self.catoperations)
            """
            This, above is super important: the operation used is relative to the counttype, and changes to use 'catoperation' instead of 'bookoperation'
            That's the place that the denominator queries avoid having to do a table scan on full bookcounts that would take hours, and instead takes
            milliseconds.
            """
            self.wordstables = " "
            self.wordswhere  = " TRUE "
            #Just a dummy thing to make the SQL writing easier. Shouldn't take any time. Will usually be extended with actual conditions.

    def set_operations(self):

        """
        This is the code that allows multiple values to be selected.
        It is definitely not as tight as it could be. Sorry everyone. A lot can be removed
        when we kill back-compatability.
        """

        backCompatability = {"Occurrences_per_Million_Words":"WordsPerMillion","Raw_Counts":"WordCount","Percentage_of_Books":"TextPercent","Number_of_Books":"TextCount"}

        for oldKey in backCompatability.keys():
            self.counttype = [re.sub(oldKey,backCompatability[oldKey],entry) for entry in self.counttype]

        self.bookoperation = {}
        self.catoperation = {}
        self.finaloperation = {}

        #Text statistics
        self.bookoperation['TextPercent'] = "count(DISTINCT " + self.prefs['fastcat'] + ".bookid) as TextCount"
        self.bookoperation['TextRatio'] = "count(DISTINCT " + self.prefs['fastcat'] + ".bookid) as TextCount"
        self.bookoperation['TextCount'] = "count(DISTINCT " + self.prefs['fastcat'] + ".bookid) as TextCount"

        #Word Statistics
        self.bookoperation['WordCount'] = "sum(main.count) as WordCount"
        self.bookoperation['WordsPerMillion'] = "sum(main.count) as WordCount"
        self.bookoperation['WordsRatio'] = "sum(main.count) as WordCount"


        """
        +Total Numbers for comparisons/significance assessments
        This is a little tricky. The total words is EITHER the denominator (as in a query against words per Million) or the numerator+denominator (if you're comparing
        Pittsburg and Pittsburgh, say, and want to know the total number of uses of the lemma. For now, "TotalWords" means the former and "SumWords" the latter,
        On the theory that 'TotalWords' is more intuitive and only I (Ben) will be using SumWords all that much.
        """
        self.bookoperation['TotalWords'] = self.bookoperation['WordsPerMillion']
        self.bookoperation['SumWords'] = self.bookoperation['WordsPerMillion']
        self.bookoperation['TotalTexts'] = self.bookoperation['TextCount']
        self.bookoperation['SumTexts'] = self.bookoperation['TextCount']

        for stattype in self.bookoperation.keys():
            if re.search("Word",stattype):
                self.catoperation[stattype] = "sum(nwords) as WordCount"
            if re.search("Text",stattype):
                self.catoperation[stattype] = "count(nwords) as TextCount"

        self.finaloperation['TextPercent'] = "IFNULL(numerator.TextCount,0)/IFNULL(denominator.TextCount,0)*100 as TextPercent"
        self.finaloperation['TextRatio'] = "IFNULL(numerator.TextCount,0)/IFNULL(denominator.TextCount,0) as TextRatio"
        self.finaloperation['TextCount'] = "IFNULL(numerator.TextCount,0) as TextCount"

        self.finaloperation['WordsPerMillion'] = "IFNULL(numerator.WordCount,0)*100000000/IFNULL(denominator.WordCount,0)/100 as WordsPerMillion"
        self.finaloperation['WordsRatio'] = "IFNULL(numerator.WordCount,0)/IFNULL(denominator.WordCount,0) as WordsRatio"
        self.finaloperation['WordCount'] = "IFNULL(numerator.WordCount,0) as WordCount"

        self.finaloperation['TotalWords'] = "IFNULL(denominator.WordCount,0) as TotalWords"
        self.finaloperation['SumWords']   = "IFNULL(denominator.WordCount,0) + IFNULL(numerator.WordCount,0) as SumWords"
        self.finaloperation['TotalTexts'] = "IFNULL(denominator.TextCount,0) as TotalTexts"
        self.finaloperation['SumTexts'] = "IFNULL(denominator.TextCount,0) + IFNULL(numerator.TextCount,0) as SumTexts"

        """
        The values here will be chosen in build_wordstables; that's what decides if it uses the 'bookoperation' or 'catoperation' dictionary to build out.
        """

        self.finaloperations = list()
        self.bookoperations = set()
        self.catoperations = set()

        for summaryStat in self.counttype:
            self.catoperations.add(self.catoperation[summaryStat])
            self.bookoperations.add(self.bookoperation[summaryStat])
            self.finaloperations.append(self.finaloperation[summaryStat])

    def counts_query(self):

        self.operation = ','.join(self.bookoperations)
        self.build_wordstables()

        countsQuery = """
            SELECT
                %(selections)s,
                %(operation)s
            FROM
                %(catalog)s
                %(main)s
                %(wordstables)s
            WHERE
                 %(catwhere)s AND %(wordswhere)s
            GROUP BY
                %(groupings)s
        """ % self.__dict__
        return countsQuery

    def bookid_query(self):
        #A temporary method to setup the hasword query.
        self.operation = ','.join(self.bookoperations)
        self.build_wordstables()

        countsQuery = """
            SELECT
                main.bookid as bookid
            FROM
                %(catalog)s
                %(main)s
                %(wordstables)s
            WHERE
                 %(catwhere)s AND %(wordswhere)s
        """ % self.__dict__
        return countsQuery

    def debug_query(self):
        query = self.ratio_query(materialize = False)
        return json.dumps(self.denominator.groupings.split(",")) + query 
    
    def query(self,materialize=False):
        """
        We launch a whole new userquery instance here to build the denominator, based on the 'compare_dictionary' option (which in most
        cases is the search_limits without the keys, see above; it can also be specially defined using asterisks as a shorthand to identify other fields to drop.
        We then get the counts_query results out of that result.
        """

        """
        self.denominator =  userquery(outside_dictionary = self.compare_dictionary,db=self.db,databaseScheme=self.databaseScheme)
        self.supersetquery = self.denominator.counts_query()
        supersetIndices = self.denominator.groupings.split(",")
        if materialize:
            self.supersetquery = derived_table(self.supersetquery,self.db,indices=supersetIndices).materialize()
        """
        self.mainquery    = self.counts_query()
        self.countcommand = ','.join(self.finaloperations)
        self.totalselections  = ",".join([group for group in self.outerGroups if group!="1 as In_Library" and group != ""])
        if self.totalselections != "": self.totalselections += ", "
       
        query = """
        SELECT
            %(totalselections)s
            %(countcommand)s
        FROM
            (%(mainquery)s) as numerator
        %(joinSuffix)s
        GROUP BY %(groupings)s;""" % self.__dict__

        return query


    def returnPossibleFields(self):
        try:
            self.cursor.execute("SELECT name,type,description,tablename,dbname,anchor FROM masterVariableTable WHERE status='public'")
            colnames = [line[0] for line in self.cursor.description]
            returnset = []
            for line in self.cursor.fetchall():
                thisEntry = {}
                for i in range(len(line)):
                    thisEntry[colnames[i]] = line[i]
                returnset.append(thisEntry)
        except:
            returnset=[]
        return returnset

    def return_slug_data(self,force=False):
        #Rather than understand this error, I'm just returning 0 if it fails.
        #Probably that's the right thing to do, though it may cause trouble later.
        #It's just a punishment for not later using a decent API call with "Raw_Counts" to extract these counts out, and relying on this ugly method.
        #Please, citizens of the future, NEVER USE THIS METHOD.
        try:
            temp_words = self.return_n_words(force = True)
            temp_counts = self.return_n_books(force = True)
        except:
            temp_words = 0
            temp_counts = 0
        return [temp_counts,temp_words]

    def return_n_books(self,force=False): #deprecated
        if (not hasattr(self,'nbooks')) or force:
            query = "SELECT count(*) from " + self.catalog + " WHERE " + self.catwhere
            silent = self.cursor.execute(query)
            self.counts = int(self.cursor.fetchall()[0][0])
        return self.counts

    def return_n_words(self,force=False): #deprecated
        if (not hasattr(self,'nwords')) or force:
            query = "SELECT sum(nwords) from " + self.catalog + " WHERE " + self.catwhere
            silent = self.cursor.execute(query)
            self.nwords = int(self.cursor.fetchall()[0][0])
        return self.nwords

    def bibliography_query(self,limit = "100"):
        #I'd like to redo this at some point so it could work as an API call more naturally.
        self.limit = limit
        self.ordertype = "sum(main.count*10000/nwords)"
        try:
            if self.outside_dictionary['ordertype'] == "random":
                if self.counttype==["Raw_Counts"] or self.counttype==["Number_of_Books"] or self.counttype==['WordCount'] or self.counttype==['BookCount'] or self.counttype==['TextCount']:
                    self.ordertype = "RAND()"
                else:
                    #This is a based on an attempt to match various different distributions I found on the web somewhere to give
                    #weighted results based on the counts. It's not perfect, but might be good enough. Actually doing a weighted random search is not easy without
                    #massive memory usage inside sql.
                    self.ordertype = "LOG(1-RAND())/sum(main.count)"
        except KeyError:
            pass

        #If IDF searching is enabled, we could add a term like '*IDF' here to overweight better selecting words
        #in the event of a multiple search.
        self.idfterm = ""
        prep = self.counts_query()


        if self.main == " ":
            self.ordertype="RAND()"

        bibQuery = """
        SELECT searchstring
        FROM """ % self.__dict__ + self.prefs['fullcat'] + """ RIGHT JOIN (
        SELECT
        """+ self.prefs['fastcat'] + """.bookid, %(ordertype)s as ordering
            FROM
                %(catalog)s
                %(main)s
                %(wordstables)s
            WHERE
                 %(catwhere)s AND %(wordswhere)s
        GROUP BY bookid ORDER BY %(ordertype)s DESC LIMIT %(limit)s
        ) as tmp USING(bookid) ORDER BY ordering DESC;
        """ % self.__dict__
        return bibQuery

    def disk_query(self,limit="100"):
        pass

    def return_books(self):
        #This preps up the display elements for a search: it returns an array with a single string for each book, sorted in the best possible way
        silent = self.cursor.execute(self.bibliography_query())
        returnarray = []
        for line in self.cursor.fetchall():
            returnarray.append(line[0])
        if not returnarray:
            #why would someone request a search with no locations? Turns out (usually) because the smoothing tricked them.
            returnarray.append("No results for this particular point: try again without smoothing")
        newerarray = self.custom_SearchString_additions(returnarray)
        return json.dumps(newerarray)

    def search_results(self):
        #This is an alias that is handled slightly differently in APIimplementation (no "RESULTS" bit in front). Once
        #that legacy code is cleared out, they can be one and the same.
        return json.loads(self.return_books())

    def getActualSearchedWords(self):
        if len(self.wordswhere) > 7:
            words = self.outside_dictionary['search_limits']['word']
            #Break bigrams into single words.
            words = ' '.join(words).split(' ')
            self.cursor.execute("""SELECT word FROM wordsheap WHERE """ + where_from_hash({self.word_field:words}))
            self.actualWords =[item[0] for item in self.cursor.fetchall()]
        else:
            self.actualWords = ["tasty","mistake","happened","here"]

    def custom_SearchString_additions(self,returnarray):
        """
        It's nice to highlight the words searched for. This will be on partner web sites, so requires custom code for different databases
        """
        db = self.outside_dictionary['database']
        if db in ('jstor','presidio','ChronAm','LOC','OL'):
            self.getActualSearchedWords()
            if db=='jstor':
                joiner = "&searchText="
                preface = "?Search=yes&searchText="
                urlRegEx = "http://www.jstor.org/stable/\d+"
            if db=='presidio' or db=='OL':
                joiner = "+"
                preface =  "#page/1/mode/2up/search/"
                urlRegEx = 'http://archive.org/stream/[^"# ><]*'
            if db in ('ChronAm','LOC'):
                preface = "/;words="
                joiner = "+"
                urlRegEx = 'http://chroniclingamerica.loc.gov[^\"><]*/seq-\d+'
            newarray = []
            for string in returnarray:
                try:
                    base = re.findall(urlRegEx,string)[0]
                    newcore = ' <a href = "' +  base  + preface + joiner.join(self.actualWords) + '"> search inside </a>'
                    string = re.sub("^<td>","",string)
                    string = re.sub("</td>$","",string)
                    string = string+newcore
                except IndexError:
                    pass
                newarray.append(string)
        #Arxiv is messier, requiring a whole different URL interface: http://search.arxiv.org:8081/paper.jsp?r=1204.3352&qs=netwokr
        else:
            newarray = returnarray
        return newarray

    def return_query_values(self,query = "ratio_query"):
        #The API returns a dictionary with years pointing to values.
        """
        DEPRECATED: use 'return_json' or 'return_tsv' (the latter only works with single 'search_limits' options) instead
        """
        values = []
        querytext = getattr(self,query)()
        silent = self.cursor.execute(querytext)
            #Gets the results
        mydict = dict(self.cursor.fetchall())
        try:
            for key in mydict.keys():
                #Only return results inside the time limits
                if key >= self.time_limits[0] and key <= self.time_limits[1]:
                    mydict[key] = str(mydict[key])
                else:
                    del mydict[key]
            mydict = smooth_function(mydict,smooth_method = self.smoothingType,span = self.smoothingSpan)

        except:
            mydict = {0:"0"}

        #This is a good place to change some values.
        try:
            return {'index':self.index, 'Name':self.words_searched,"values":mydict,'words_searched':""}
        except:
            return{'values':mydict}


    def return_tsv(self,query = "ratio_query"):
        if self.outside_dictionary['counttype']=="Raw_Counts" or self.outside_dictionary['counttype']==["Raw_Counts"]:
            query="counts_query"
            #This allows much speedier access to counts data if you're willing not to know about all the zeroes.
            #Will not work as well once the id_fields are in use.
        querytext = getattr(self,query)()
        silent = self.cursor.execute(querytext)
        results = ["\t".join([to_unicode(item[0]) for item in self.cursor.description])]
        lines = self.cursor.fetchall()
        for line in lines:
            items = []
            for item in line:
                item = to_unicode(item)
                item = re.sub("\t","<tab>",item)
                items.append(item)
            results.append("\t".join(items))
        return "\n".join(results)

    def export_data(self,query1="ratio_query"):
        self.smoothing=0
        return self.return_query_values(query=query1)

    def execute(self):
        #This performs the query using the method specified in the passed parameters.
        if self.method=="Nothing":
            pass
        else:
            value = getattr(self,self.method)()
            return value

class derived_table(object):
    """
    MySQL/MariaDB doesn't have good subquery materialization,
    so I'm implementing it by hand.
    """
    def __init__(self,SQLstring,db,indices = [],dbToPutIn = "bookworm_scratch"):
        """
        initialize with the code to create the table; the database it will be in
        (to prevent conflicts with other identical queries in other dbs);
        and the list of all tables to be indexed
        (optional, but which can really speed up joins)
        """
        self.query = SQLstring
        self.db = db
        #Each query is identified by a unique key hashed
        #from the query and the dbname.
        self.queryID  = dbToPutIn + "." + "derived" + hashlib.sha1(self.query + db.dbname).hexdigest()
        self.indices = "(" + ",".join(["INDEX(%s)" % index  for index in indices]) + ")" if indices != [] else ""
    
    def setStorageEngines(self,temp):
        """
        Chooses where and how to store tables.
        """
        self.tempString = "TEMPORARY" if temp else ""
        self.engine = "MEMORY" if temp else "MYISAM"

    def checkCache(self):
        """
        Checks what's already been calculated.
        """
        try:
            (self.count,self.created,self.modified,self.createCode,self.data) = self.db.cursor.execute("SELECT count,created,modified,createCode,data FROM bookworm_scratch.cache WHERE fieldname='%s'" %self.queryID)[0]
            return True
        except:
            (self.count,self.created,self.modified,self.createCode,self.data) = [None]*5
            return False

    def fillTableWithData(self,data):
        dataCode = "INSERT INTO %s values ("%self.queryID + ", ".join(["%s"]*len(data[0])) + ")"
        self.db.cursor.executemany(dataCode,data)
        self.db.db.commit()
            
    def materializeFromCache(self,temp):
        if self.data is not None:
            #Datacode should never exist without createCode also.
            self.db.cursor.execute(self.createCode)
            self.fillTableWithData(pickle.loads(self.data,protocol=-1))
            return True
        else:
            return False


    def createFromCacheWithDataFromBookworm(self,temp,postDataToCache=False):
        """
        If the create code exists but the data does not.
        This uses a form of query that MySQL can cache,
        unlike the normal subqueries OR the CREATE TABLE ... INSERT
        used by materializeFromBookworm.

        You can also post the data itself, but that's turned off by default:
        because why wouldn't it have been posted the first time?
        Probably it's too large or something, is why.
        """
        if self.createCode==None:
            return False
        self.db.cursor.execute(self.createCode)
        self.db.cursor.execute(self.query)
        data = [row for row in self.db.cursor.fetchall()]
        self.newdata = pickle.dumps(data,protocol=-1)
        self.fillTableWithData(data)
        if postDataToCache:
            self.updateCache(postQueries=["UPDATE bookworm_scratch.cache SET data='%s' WHERE fieldname='%s'" %(MySQLdb.escape_string(self.newdata),self.queryID)])
        else:
            self.updateCache()
        return True
            
    def materializeFromBookworm(self,temp,postDataToCache=True,postCreateToCache=True):
        import cPickle as pickle
        self.db.cursor.execute("CREATE %(tempString)s TABLE %(queryID)s %(indices)s ENGINE=%(engine)s %(query)s;" % self.__dict__)
        self.db.cursor.execute("SHOW CREATE TABLE %s" %self.queryID)
        self.newCreateCode = self.db.cursor.fetchall()[0][1]
        self.db.cursor.execute("SELECT * FROM %s" %self.queryID)
        #coerce the results to a list of tuples, then pickle it.
        self.newdata = pickle.dumps([row for row in self.db.cursor.fetchall()],protocol=-1)

        if postDataToCache:
            self.updateCache(postQueries=["UPDATE bookworm_scratch.cache SET data='%s',createCode='%s' WHERE fieldname='%s'" %(MySQLdb.escape_string(self.newdata),MySQLdb.escape_string(self.newCreateCode),self.queryID)])

        if postCreateToCache:
            self.updateCache(postQueries=["UPDATE bookworm_scratch.cache SET createCode='%s' WHERE fieldname='%s'" %(MySQLdb.escape_string(self.newCreateCode),self.queryID)])
        
        
    def updateCache(self,postQueries=[]):
        q1 = """
        INSERT INTO bookworm_scratch.cache (fieldname,created,modified,count) VALUES
        ('%s',NOW(),NOW(),1) ON DUPLICATE KEY UPDATE count = count + 1,modified=NOW();""" %self.queryID
        result = self.db.cursor.execute(q1)
        for query in postQueries:
            self.db.cursor.execute(query)
        self.db.db.commit()
        
    def materialize(self,temp="default"):
        """
        materializes the table, by default in memory in the bookworm_scratch
        database. If temp is false, the table will be stored on disk, available
        for future users too. This should be used sparingly, because you can't have too many
        tables on disk.

        Returns the tableID, which the superquery to this one may need to know.
        """
        if temp=="default":
            temp=True

        self.checkCache()
        self.setStorageEngines(temp)

        try:
            if not self.materializeFromCache(temp):
                if not self.createFromCacheWithDataFromBookworm(temp):
                    self.materializeFromBookworm(temp)
    
        except MySQLdb.OperationalError,e:
            #Often the error will be 1050, which is a good thing:
            #It means we don't need to
            #create the table, because it's there already.
            #But if it's not, something bad is happening.
            if not re.search("1050.*already exists",str(e)):
                raise
        
        return self.queryID
        
class databaseSchema:
    """
    This class stores information about the database setup that is used to optimize query creation query
    and so that queries know what tables to include.
    It's broken off like this because it might be usefully wrapped around some of the backend features,
    because it shouldn't be run multiple times in a single query (that spawns two instances of itself), as was happening before.

    It's closely related to some of the classes around variables and variableSets in the Bookworm Creation scripts,
    but is kept separate for now: that allows a bit more flexibility, but is probaby a Bad Thing in the long run.
    """

    def __init__(self,db):
        self.db = db
        self.cursor=db.cursor
        #has of what table each variable is in
        self.tableToLookIn = {}
        #hash of what the root variable for each search term is (eg, 'author_birth' might be crosswalked to 'authorid' in the main catalog.)
        self.anchorFields = {}
        #aliases: a hash showing internal identifications codes that dramatically speed up query time, but which shouldn't be exposed.
        #So you can run a search for "state," say, and the database will group on a 50-element integer code instead of a VARCHAR that
        #has to be long enough to support "Massachusetts" and "North Carolina."
        #A couple are hard-coded in, but most are derived by looking for fields that end in the suffix "__id" later.

        if self.db.dbname=="presidio":
            self.aliases = {"classification":"lc1","lat":"pointid","lng":"pointid"}
        else:
            self.aliases = dict()
            
        try:
            #First build using the new streamlined tables; if that fails, 
            #build using the old version that hits the INFORMATION_SCHEMA,
            #which is bad practice.
            self.newStyle(db)
        except:
            #The new style will fail on old bookworms: a failure is an easy way to test
            #for oldness, though of course something else might be causing the failure.
            self.oldStyle(db)
        
        
    def newStyle(self,db):
        self.tableToLookIn['bookid'] = 'fastcat'
        self.anchorFields['bookid'] = 'fastcat'
        self.anchorFields['wordid'] = 'wordid'
        self.tableToLookIn['wordid'] = 'wordsheap'


        tablenames = dict()
        tableDepends = dict()
        db.cursor.execute("SELECT dbname,alias,tablename,dependsOn FROM masterVariableTable JOIN masterTableTable USING (tablename);")
        for row in db.cursor.fetchall():
            (dbname,alias,tablename,dependsOn) = row
            self.tableToLookIn[dbname] = tablename
            self.anchorFields[tablename] = dependsOn
            self.aliases[dbname] = alias

    def oldStyle(self,db):

        #This is sorted by engine DESC so that memory table locations will overwrite disk table in the hash.

        self.cursor.execute("SELECT ENGINE,TABLE_NAME,COLUMN_NAME,COLUMN_KEY,TABLE_NAME='fastcat' OR TABLE_NAME='wordsheap' AS privileged FROM information_schema.COLUMNS JOIN INFORMATION_SCHEMA.TABLES USING (TABLE_NAME,TABLE_SCHEMA) WHERE TABLE_SCHEMA='%(dbname)s' ORDER BY privileged,ENGINE DESC,TABLE_NAME,COLUMN_KEY DESC;" % self.db.__dict__);
        columnNames = self.cursor.fetchall()

        parent = 'bookid'
        previous = None
        for databaseColumn in columnNames:
            if previous != databaseColumn[1]:
                if databaseColumn[3]=='PRI' or databaseColumn[3]=='MUL':
                    parent = databaseColumn[2]
                    previous = databaseColumn[1]
                else:
                    parent = 'bookid'
            else:
                self.anchorFields[databaseColumn[2]]  = parent
                if databaseColumn[3]!='PRI' and databaseColumn[3]!="MUL": #if it's a primary key, this isn't the right place to find it.
                    self.tableToLookIn[databaseColumn[2]] = databaseColumn[1]
                if re.search('__id\*?$',databaseColumn[2]):
                    self.aliases[re.sub('__id','',databaseColumn[2])]=databaseColumn[2]

        try:
            cursor = self.cursor.execute("SELECT dbname,tablename,anchor,alias FROM masterVariableTables")
            for row in cursor.fetchall():
                if row[0] != row[3]:
                    self.aliases[row[0]] = row[3]
                if row[0] != row[2]:
                    self.anchorFields[row[0]] = row[2]
                #Should be uncommented, but some temporary issues with the building script
                #self.tableToLookIn[row[0]] = row[1]
        except:
            pass
        self.tableToLookIn['bookid'] = 'fastcat'
        self.anchorFields['bookid'] = 'fastcat'
        self.anchorFields['wordid'] = 'wordid'
        self.tableToLookIn['wordid'] = 'wordsheap'
    #############
    ##GENERAL#### #These are general purpose functional types of things not implemented in the class.
    #############

def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    elif isinstance(obj,int):
        obj=unicode(str(obj),encoding)
    else:
        obj = unicode(str(obj),encoding)
    return obj

def where_from_hash(myhash,joiner=" AND ",comp = " = ",escapeStrings=True):
    whereterm = []
    #The general idea here is that we try to break everything in search_limits down to a list, and then create a whereterm on that joined by whatever the 'joiner' is ("AND" or "OR"), with the comparison as whatever comp is ("=",">=",etc.).
    #For more complicated bits, it gets all recursive until the bits are all in terms of list.
    for key in myhash.keys():
        values = myhash[key]
        if isinstance(values,basestring) or isinstance(values,int) or isinstance(values,float):
            #This is just human-being handling. You can pass a single value instead of a list if you like, and it will just convert it
            #to a list for you.
            values = [values]
        #Or queries are special, since the default is "AND". This toggles that around for a subportion.
        if key=='$or' or key=="$OR":
            for comparison in values:
                whereterm.append(where_from_hash(comparison,joiner=" OR ",comp=comp))
                #The or doesn't get populated any farther down.
        elif isinstance(values,dict):
            #Certain function operators can use MySQL terms. These are the only cases that a dict can be passed as a limitations
            operations = {"$gt":">","$ne":"!=","$lt":"<","$grep":" REGEXP ","$gte":">=","$lte":"<=","$eq":"="}
            for operation in values.keys():
                whereterm.append(where_from_hash({key:values[operation]},comp=operations[operation],joiner=joiner))
        elif isinstance(values,list):
            #and this is where the magic actually happens: the cases where the key is a string, and the target is a list.
            if isinstance(values[0],dict):
                # If it's a list of dicts, then there's one thing that happens. Currently all types are assumed to be the same:
                # you couldn't pass in, say {"year":[{"$gte":1900},1898]} to catch post-1898 years except for 1899. Not that you
                # should need to.
                for entry in values:
                    whereterm.append(where_from_hash(entry))
            else:
                #Note that about a third of the code is spent on escaping strings.
                if escapeStrings:
                    if isinstance(values[0],basestring):
                        quotesep="'"
                    else:
                        quotesep = ""
                    def escape(value): return MySQLdb.escape_string(to_unicode(value))
                else:
                    def escape(value): return to_unicode(value)
                    quotesep=""

                #Note the "OR" here. There's no way to pass in a query like "year=1876 AND year=1898" as currently set up.
                #Obviously that's no great loss, but there might be something I'm missing that would be desire a similar format somehow.
                #(In cases where the same book could have two different years associated with it)
                whereterm.append(" (" + " OR ".join([" (" + key+comp+quotesep+escape(value)+quotesep+") " for value in values])+ ") ")
    return "(" + joiner.join(whereterm) + ")"
    #This works pretty well, except that it requires very specific sorts of terms going in, I think.



#I'd rather have all this smoothing stuff done at the client side, but currently it happens here.

#The idea is: this works by default by slurping up from the command line, but you could also load the functions in and run results on your own queries.
try:
    command = str(sys.argv[1])
    command = json.loads(command)
#Got to go before we let anything else happen.
    p = userqueries(command)
    result = p.execute()
    print json.dumps(result)
except:
    pass



def debug(string):
    """
    Makes it easier to debug through a web browser by handling the headers.
    Despite being called a `string`, it can be anything that python can print.
    """
    print headers('1')
    print "<br>"
    print string
    print "<br>"
