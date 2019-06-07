#!/usr/local/bin/python

from .variableSet import to_unicode
from .search_limits import Search_limits
from .bwExceptions import BookwormException

import json
import re
import copy
import MySQLdb
import hashlib
import logging



# If you have bookworms stored on a different host, you can create more lines
# like this.
# A different host and read_default_file will let you import things onto a
# different server.

class DbConnect(object):
    # This is a read-only account
    def __init__(self, database=None,
                 host=None):
        
        self.dbname = database
        
        import bookwormDB.configuration
        conf = bookwormDB.configuration.Configfile("read_only").config

        if database is None:
            raise BookwormException("You must specify a database")

        connargs = {
            "db": database,
            "use_unicode": 'True',
            "charset": 'utf8',
            "user": conf.get("client", "user"),
            "password": conf.get("client", "password")
        }

        if host:
            connargs['host'] = host
        # For back-compatibility:
        else:
            connargs['host'] = "localhost"

        try:
            self.db = MySQLdb.connect(**connargs)
        except:
            try:
                # Sometimes mysql wants to connect over this rather than a socket:
                # falling back to it for backward-compatibility.                
                connargs["host"] = "127.0.0.1"
                self.db = MySQLdb.connect(**connargs)
            except:
                raise
            
        self.cursor = self.db.cursor()

def fail_if_nonword_characters_in_columns(input):
    keys = all_keys(input)
    for key in keys:
        if re.search(r"[^A-Za-z_$*0-9]", key):
            logging.error("{} has nonword character".format(key))
            raise


def all_keys(input):
    """
    Recursive function. Get every keyname in every descendant of a dictionary.
    Iterates down on list and dict structures to search for more dicts with
    keys.
    """
    values = []
    if isinstance(input, dict):
        values = list(input.keys())
        for key in list(input.keys()):
            values = values + all_keys(input[key])
    if isinstance(input, list):
        for value in input:
            valleys = all_keys(value)
            for val in valleys:
                values.append(val)
    return values

# The basic object here is a 'Query:' it takes dictionary as input,
# as defined in the API, and returns a value
# via the 'execute' function whose behavior
# depends on the mode that is passed to it.
# Given the dictionary, it can return a number of objects.
# The "Search_limits" array in the passed dictionary determines how many
# elements it returns; this lets multiple queries be bundled together.
# Most functions describe a subquery that might be combined into one big query
# in various ways.

def check_query(query):

    
    fail_if_nonword_characters_in_columns(query)

    for key in ['database']:
        if not key in query:
            raise BookwormException({"code": 400, "message": "You must specify a value for {}".format(key)})


    if query['method'] in ["schema", "search"]:
        # Queries below this only apply to "data"
        return
    
    for v in query['counttype']:
        if not v in ['WordCount', 'TextCount']:
            raise BookwormException({"code": 400, "message": 'Only "WordCount" and "TextCount"'
                                     ' counts are supported by the SQL api, but passed {}'.format(v)})
    

class Query(object):
    """
    The base class for a bookworm search.
    """
    def __init__(self, query_object = {}, db = None, databaseScheme = None):
        # Certain constructions require a DB connection already available, so we just start it here, or use the one passed to it.

        check_query(query_object)
        
        self.prefs = {'database': query_object['database']}
        
        self.query_object = query_object
        
        self.db = db
        if db is None:
            self.db = DbConnect(query_object['database'])
            
        self.databaseScheme = databaseScheme
        if databaseScheme is None:
            self.databaseScheme = databaseSchema(self.db)

        self.cursor = self.db.cursor

        # Some tablenames.
        
        self.wordsheap = self.databaseScheme.fallback_table('wordsheap')
        self.fastcat = self.databaseScheme.fallback_table("fastcat")
        logging.info("Catalog set to {}".format(self.fastcat))
        self.words = "words"

        self.defaults(query_object) # Take some defaults
        
        self.derive_variables() # Derive some useful variables that the query will use.

    def defaults(self, query_object):
        # these are default values;these are the only values that can be set in the query
        # search_limits is an array of dictionaries;
        # each one contains a set of limits that are mutually independent
        # The other limitations are universal for all the search limits being set.



        self.wordsTables = None
    
        
        # Set up a dictionary for the denominator of any fraction if it doesn't already exist:
        self.search_limits = query_object.setdefault('search_limits', [{"word":["polka dot"]}])
        self.words_collation = query_object.setdefault('words_collation', "Case_Insensitive")

        lookups = {"Case_Insensitive":'word', 'lowercase':'lowercase', 'casesens':'casesens', "case_insensitive":"word", "Case_Sensitive":"casesens", "All_Words_with_Same_Stem":"stem", 'stem':'stem'}
        self.word_field = lookups[self.words_collation]

        self.time_limits = query_object.setdefault('time_limits', [0, 10000000])
        self.time_measure = query_object.setdefault('time_measure', 'year')

        self.groups = set()
        self.outerGroups = []
        self.finalMergeTables = set()

        try:
            groups = query_object['groups']
        except:
            groups = None
            
        if groups == [] or groups == ["unigram"]:
            # Set an arbitrary column name that will always be true if nothing else is set.
            pass
        #            groups.insert(0, "1 as In_Library")

        if groups is None:
            # A user query can't demand ungrouped results,
            # but internally it's represented as None.
            groups = []
            
        for group in groups:

            # There's a special set of rules for how to handle unigram and bigrams
            multigramSearch = re.match("(unigram|bigram|trigram)(\d)?", group)

            if multigramSearch:
                if group == "unigram":
                    gramPos = "1"
                    gramType = "unigram"

                else:
                    gramType = multigramSearch.groups()[0]
                    try:
                        gramPos = multigramSearch.groups()[1]
                    except:
                        print("currently you must specify which bigram element you want (eg, 'bigram1')")
                        raise

                lookupTableName = "%sLookup%s" %(gramType, gramPos)
                self.outerGroups.append("%s.%s as %s" %(lookupTableName, self.word_field, group))
                self.finalMergeTables.add(" JOIN %s as %s ON %s.wordid=w%s" %(self.wordsheap, lookupTableName, lookupTableName, gramPos))
                self.groups.add("words%s.wordid as w%s" %(gramPos, gramPos))

            else:
                self.outerGroups.append(group)
                try:
                    if self.databaseScheme.aliases[group] != group:
                        # Search on the ID field, not the basic field.
                        # debug(self.databaseScheme.aliases.keys())
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
        self.groupings = ",".join([group for group in self.groups])

        self.joinSuffix = "" + " ".join(self.finalMergeTables)

        """
        Define the comparison set if a comparison is being done.
        """

        self.counttype = query_object.setdefault('counttype', ["WordCount"])

        if isinstance(self.counttype, (str, bytes)):
            self.counttype = [self.counttype]

    def determineOutsideDictionary(self):
        """
        deprecated--tagged for deletion.
        """
        self.compare_dictionary = copy.deepcopy(self.query_object)
        if 'compare_limits' in list(self.query_object.keys()):
            self.compare_dictionary['search_limits'] = self.query_object['compare_limits']
            del self.query_object['compare_limits']
        elif sum([bool(re.search(r'\*', string)) for string in list(self.query_object['search_limits'].keys())]) > 0:
            # If any keys have stars at the end, drop them from the compare set
            # This is often a _very_ helpful definition for succinct comparison queries of many types.
            # The cost is that an asterisk doesn't allow you

            for key in list(self.query_object['search_limits'].keys()):
                if re.search(r'\*', key):
                    # rename the main one to not have a star
                    self.query_object['search_limits'][re.sub(r'\*', '', key)] = self.query_object['search_limits'][key]
                    # drop it from the compare_limits and delete the version in the search_limits with a star
                    del self.query_object['search_limits'][key]
                    del self.compare_dictionary['search_limits'][key]
        else: # if nothing specified, we compare the word to the corpus.
            deleted = False
            for key in list(self.query_object['search_limits'].keys()):
                if re.search('words?\d', key) or re.search('gram$', key) or re.match(r'word', key):
                    del self.compare_dictionary['search_limits'][key]
                    deleted = True
            if not deleted:
                # If there are no words keys, just delete the first key of any type.
                # Sort order can't be assumed, but this is a useful failure mechanism of last resort. Maybe.
                try:
                    del self.compare_dictionary['search_limits'][list(self.query_object['search_limits'].keys())[0]]
                except:
                    pass
        """
        The grouping behavior here is not desirable, but I'm not quite sure how yet.
        Aha--one way is that it accidentally drops out a bunch of options. I'm just disabling it: let's see what goes wrong now.
        """

    def derive_variables(self):
        # These are locally useful, and depend on the search limits put in.
        self.limits = self.search_limits
        
        # Treat empty constraints as nothing at all, not as restricting to the set of nothing.
        for key in list(self.limits.keys()):
            if self.limits[key] == []:
                del self.limits[key]

        if 'word' in self.limits:
            self.word_limits = True
        else:
            self.word_limits = False
                
        self.set_operations()
        
        self.create_catalog_table()
        
        self.make_catwhere()
        
        self.make_wordwheres()

    def tablesNeededForQuery(self, fieldNames=[]):
        """
        Deprecated.
        """
        db = self.db
        neededTables = set()
        tablenames = dict()
        tableDepends = dict()
        
        q = "SELECT dbname,alias,tablename,dependsOn FROM masterVariableTable JOIN masterTableTable USING (tablename);"
        logging.debug(q)
        db.cursor.execute(q)
        for row in db.cursor.fetchall():
            tablenames[row[0]] = row[2]
            tableDepends[row[2]] = row[3]

        for fieldname in fieldNames:
            parent = ""
            try:
                current = tablenames[fieldname]
                neededTables.add(current)
                n = 1
                while parent not in ['fastcat', 'wordsheap']:
                    parent = tableDepends[current]
                    neededTables.add(parent)
                    current = parent
                    n+=1
                    if n > 100:
                        raise TypeError("Unable to handle this; seems like a recursion loop in the table definitions.")
                    # This will add 'fastcat' or 'wordsheap' exactly once per entry
            except KeyError:
                pass

        return neededTables

    def needed_columns(self):
        """
        Given a query, what are the columns that the compiled search will need materialized?

        Important for joining appropriate tables to the search.

        Needs a recursive function so it will find keys deeply nested inside "$or" searches.
        """
        cols = []
        
        def pull_keys(entry):
            val = []
            if isinstance(entry,list) and not isinstance(entry,(str, bytes)):
                for element in entry:
                    val += pull_keys(element)
            elif isinstance(entry,dict):
                for k,v in entry.items():
                    if k[0] != "$":
                        val.append(k)
                    else:
                        val += pull_keys(v)
            else:
                return []
            
            return [re.sub(" .*","",key) for key in val]
        
        return pull_keys(self.limits)

    def wordid_query(self):
        return self.wordswhere

        if self.wordswhere != " TRUE ":
            f = "SELECT wordid FROM {words} as words1 WHERE {wordswhere}".format(**self.__dict__)
            logging.debug("`" + self.wordswhere + "`")            
            return " wordid IN ({})".format(f)
        else:
            return " TRUE "
    
    def make_group_query(self):
        aliases = [self.databaseScheme.aliases[g] for g in self.query_object["groups"]]
        if len(aliases) > 0:
            return "GROUP BY {}".format(", ".join(aliases))
        else:
            return " "


    def main_table(self):
        if self.gram_size() == 1:
            return 'master_bookcounts as main'
        if self.gram_size() == 2:
            return 'master_bigrams as main'
        
    def full_query_tables(self):
        # Joins are needed to provide groups, but *not* to provide
        # provide evidence for wheres.

        # But if there's a group, there may also need to be an associated where.
        
        if self.word_limits == False:
            tables = [self.fastcat]
        else:
            tables = [self.main_table()]


        cols = self.query_object['groups']
        ts = self.databaseScheme.tables_for_variables(cols)

        for t in ts:
            if not t in tables:
                tables.append(t)

        return tables
        
    def make_join_query(self):
        tables = self.full_query_tables()
        return " NATURAL JOIN ".join(tables)


    def base_query(self):
        dicto = {}
        dicto['finalGroups'] = ', '.join(self.query_object['groups'])
        if dicto['finalGroups'] != '':
            dicto['finalGroups'] = ", " + dicto['finalGroups']
        
        dicto['group_query'] = self.make_group_query()
        dicto['op'] = ', '.join(self.set_operations())
        dicto['bookid_where'] = self.bookid_query()
        dicto['wordid_where'] = self.wordid_query()
        dicto['tables'] = self.make_join_query()
        logging.info("'{}'".format(dicto['tables']))
        
        dicto['catwhere'] = self.make_catwhere("main")
        
        basic_query = """
        SELECT {op} {finalGroups}
        FROM {tables}
        WHERE
          {bookid_where}
          AND 
          {wordid_where}
          AND {catwhere} 
        {group_query}
        """.format(**dicto)
        
        return basic_query
    
    def create_catalog_table(self):
        # self.catalog = self.prefs['fastcat'] # 'catalog' # Can be replaced with a more complicated query in the event of longer joins.

        """
         
        This should check query constraints against a list of tables, and
        join to them.  So if you query with a limit on LCSH, and LCSH
        is listed as being in a separate table, it joins the table
        "LCSH" to catalog; and then that table has one column, ALSO
        called "LCSH", which is matched against. This allows a bookid
        to be a member of multiple catalogs.

        """

        self.relevantTables = set()

        databaseScheme = self.databaseScheme
        
        cols = self.needed_columns()
        cols = [c for c in cols if not c in ["word", "word1", "word2"]]
        
        self.relevantTables = self.databaseScheme.tables_for_variables(cols)
        
        # moreTables = self.tablesNeededForQuery(columns)

        
        self.catalog = " NATURAL JOIN ".join(self.relevantTables)
        return self.catalog
#        for table in self.relevantTables:
#            if table!="fastcat" and table!="words" and table!="wordsheap" and table!="master_bookcounts" and table!="master_bigrams" and table != "fastcat_" and table != "wordsheap_":
#                self.catalog = self.catalog + """ NATURAL JOIN """ + table + " "#
#
#        return self.catalog

        
    def make_catwhere(self, query = "sub"):
        # Where terms that don't include the words table join. Kept separate so that we can have subqueries only working on one half of the stack.
        catlimits = dict()
        
        for key in list(self.limits.keys()):
            # !!Warning--none of these phrases can be used in a bookworm as a custom table names.
            
            if key not in ('word', 'word1', 'word2', 'hasword') and not re.search("words\d", key):
                catlimits[key] = self.limits[key]

        if query == "main":
            ts = set(self.full_query_tables())                
            for key in list(catlimits.keys()):
                    logging.debug(key)
                    logging.debug(ts)
                    if not (key in ts or key + "__id" in ts):
                        logging.info("removing {}".format(key))
                        del catlimits[key]
                
        if len(list(catlimits.keys())) > 0:
            catwhere = where_from_hash(catlimits)
        else:
            catwhere = "TRUE"
        if query == "sub":
            self.catwhere = catwhere
        return catwhere
    
    def gram_size(self):
        try:
            ls = [phrase.split() for phrase in self.limits['word']]
        except:
            return 0
        lengths = list(set(map(len, ls)))
        if len(lengths) > 1:
            raise BookwormException('400', 'Must pass all unigrams or all bigrams')
        else:
            return lengths[0]
            
        
        
    def make_wordwheres(self):
        self.wordswhere = " TRUE "
        
        limits = []
        
        if self.word_limits:
            """

            This doesn't currently allow mixing of one and two word searches
            together in a logical way.  It might be possible to just
            join on both the tables in MySQL--I'm not completely sure
            what would happen.  But the philosophy has been to keep
            users from doing those searches as far as possible in any
            case.

            """


            
            for phrase in self.limits['word']:
                locallimits = dict()
                array = phrase.split()
                for n, word in enumerate(array):
                    searchingFor = word
                    if self.word_field == "stem":
                        from nltk import PorterStemmer
                        searchingFor = PorterStemmer().stem_word(searchingFor)
                    if self.word_field == "case_insensitive" or \
                       self.word_field == "Case_Insensitive":
                        # That's a little joke. Get it?
                        searchingFor = searchingFor.lower()

                    
                    selectString = "SELECT wordid FROM %s WHERE %s = %%s" % (self.wordsheap, self.word_field)
                    logging.debug(selectString)
                    cursor = self.db.cursor
                    cursor.execute(selectString,(searchingFor,))

                    # Set the search key being used.
                    search_key = "wordid"
                    if self.gram_size() > 1:
                        # 1-indexed entries in the bigram tables.
                        search_key = "word{}".format(n + 1)
                    
                    for row in cursor.fetchall():
                        wordid = row[0]
                        try:
                            locallimits[search_key] += [wordid]
                        except KeyError:
                            locallimits[search_key] = [wordid]

                if len(locallimits) > 0:
                    limits.append(where_from_hash(locallimits, comp = " = ", escapeStrings=False))
                    

            self.wordswhere = "(" + ' OR '.join(limits) + ")"
            if limits == []:
                # In the case that nothing has been found, tell it explicitly to search for
                # a condition when nothing will be found.
                self.wordswhere = "bookid = -1"

        wordlimits = dict()

        limitlist = copy.deepcopy(list(self.limits.keys()))

        for key in limitlist:
            if re.search("words\d", key):
                wordlimits[key] = self.limits[key]
                self.max_word_length = max(self.max_word_length, 2)
                del self.limits[key]

        if len(list(wordlimits.keys())) > 0:
            self.wordswhere = where_from_hash(wordlimits)

        return self.wordswhere

    def build_wordstables(self):
        # Deduce the words tables we're joining against.
        # The iterating on this can be made more general to get 3 or four grams in pretty easily.
        # This relies on a determination already having been made about whether
        # this is a unigram or bigram search; that's reflected in the self.selections
        # variable.

        if self.wordsTables is not None:
            return
        
        needsBigrams = (self.max_word_length == 2 or re.search("words2", self.selections))
        
        needsUnigrams = self.max_word_length == 1;

        if self.max_word_length > 2:
            err = dict(code=400, message="Phrase is longer than what Bookworm currently supports")
            raise BookwormException(err)

        if needsBigrams:
            self.main = '''
                 master_bigrams as main
            '''

            self.wordstables = """
            JOIN %(wordsheap)s as words1 ON (main.word1 = words1.wordid)
            JOIN %(wordsheap)s as words2 ON (main.word2 = words2.wordid) """ % self.__dict__

        # I use a regex here to do a blanket search for any sort of word limitations. That has some messy sideffects (make sure the 'hasword'
        # key has already been eliminated, for example!) but generally works.

        elif needsUnigrams:
            self.main = '''
            master_bookcounts as main
            '''

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

            Call this OLAP, if you like.
            """
            self.main = " "
            self.operation = ','.join(self.set_operations(with_words = False))
            """
            This, above is super important: the operation used is relative to the counttype, and changes to use 'catoperation' instead of 'bookoperation'
            That's the place that the denominator queries avoid having to do a table scan on full bookcounts that would take hours, and instead takes
            milliseconds.
            """
            self.wordstables = " "
            self.wordswhere = " TRUE "
            # Just a dummy thing to make the SQL writing easier. Shouldn't take any time. Will usually be extended with actual conditions.

    def set_operations(self):

        with_words = self.word_limits
        
        output = []

        # experimental
        if self.query_object['counttype'] == 'bookid':
            return ['bookid']
        
        if self.query_object['counttype'] == 'wordid':
            return ['wordid']        

        
        if with_words:
            if "TextCount" in self.query_object['counttype']:
                output.append("count(DISTINCT main.bookid) as TextCount")
            if "WordCount" in self.query_object['counttype']:
                output.append("sum(main.count) as WordCount")
        else:
            if "WordCount" in self.query_object['counttype']:
                output.append("sum(nwords) as WordCount")
            if "TextCount" in self.query_object['counttype']:
                output.append("count(nwords) as TextCount")

        return output

    def bookid_query(self):
        
        q = "SELECT bookid FROM {catalog} WHERE {catwhere}""".format(**self.__dict__)

        logging.warning("'{}'".format(self.catwhere))
        
        if self.catwhere == "TRUE":
            self.bookid_where = " TRUE "
            
        else:
            self.bookid_where = " bookid IN ({}) ".format(q)

        
        return self.bookid_where
    
    def query(self):
        
        """
        Return the SQL query that fills the API request.

        There must be a search method filled out.
        """
        
        if (self.query_object['method'] == 'schema'):
            return "SELECT name,type,description,tablename,dbname,anchor FROM masterVariableTable WHERE status='public'"
        elif (self.query_object['method'] == 'search'):
            return self.bibliography_query()
        elif self.query_object['method'] == 'data':
            return self.base_query()
        else:
            raise BookwormException('400', 'Must enter "schema", "search", or "data" as method')


    def bibliography_query(self, limit = "100"):
        # I'd like to redo this at some point so it could work as an API call more naturally.
        self.limit = limit
        self.ordertype = "sum(main.count*10000/nwords)"
        try:
            if self.query_object['ordertype'] == "random":
                if self.counttype in [
                        "WordCount"
                ]:
                    self.ordertype = "RAND()"
                else:
                    # This is a based on an attempt to match various
                    # different distributions I found on the web somewhere to give
                    # weighted results based on the counts. It's not perfect, but might
                    # be good enough. Actually doing a weighted random search is not easy without
                    # massive memory usage inside sql.
                    self.ordertype = "RAND()"
                    # self.ordertype = "LOG(1-RAND())/sum(main.count)"
        except KeyError:
            pass

        # If IDF searching is enabled, we could add a term like '*IDF' here to overweight better selecting words
        # in the event of a multiple search.
        self.idfterm = ""
        prep = self.base_query()

#        if self.main == " ":
#            self.ordertype = "RAND()"

        dicto = {
            'fastcat': self.fastcat,
            'tables': self.make_join_query(),
            'ordertype': self.ordertype,
            'catwhere': self.make_catwhere("main"),
            'limit': limit
        }
        
        dicto['bookid_where'] = self.bookid_query()
        dicto['wordid_where'] = self.wordid_query()
            
        bibQuery = """
        SELECT searchstring
        FROM catalog RIGHT JOIN (
        SELECT {fastcat}.bookid, {ordertype} as ordering
            FROM
               {tables}
            WHERE
               {bookid_where} AND {wordid_where} and {catwhere}
        GROUP BY bookid ORDER BY {ordertype} DESC LIMIT {limit}
        ) as tmp USING (bookid) ORDER BY ordering DESC;
        """.format(**dicto)
        return bibQuery

    def search_results(self):
        # This is an alias that is handled slightly differently in
        # APIimplementation (no "RESULTS" bit in front). Once
        # that legacy code is cleared out, they can be one and the same.
        
        return json.loads(self.return_books())

    def getActualSearchedWords(self):
        # 
        if len(self.wordswhere) > 7:
            words = self.query_object['search_limits']['word']
            # Break bigrams into single words.
            words = ' '.join(words).split(' ')
            q = "SELECT word FROM {} WHERE {}".format(self.wordsheap, where_from_hash({self.word_field:words}))
            logging.debug(q)
            self.cursor.execute(q)
            self.actualWords = [item[0] for item in self.cursor.fetchall()]
        else:
            raise TypeError("Suspiciously low word count")
            self.actualWords = ["tasty", "mistake", "happened", "here"]

    def custom_SearchString_additions(self, returnarray):
        """
        It's nice to highlight the words searched for. This will be on partner web sites, so requires custom code for different databases
        """
        db = self.query_object['database']
        if db in ('jstor', 'presidio', 'ChronAm', 'LOC', 'OL'):
            self.getActualSearchedWords()
            if db == 'jstor':
                joiner = "&searchText="
                preface = "?Search=yes&searchText="
                urlRegEx = "http://www.jstor.org/stable/\d+"
            if db == 'presidio' or db == 'OL':
                joiner = "+"
                preface = "# page/1/mode/2up/search/"
                urlRegEx = 'http://archive.org/stream/[^"# ><]*'
            if db in ('ChronAm', 'LOC'):
                preface = "/;words="
                joiner = "+"
                urlRegEx = 'http://chroniclingamerica.loc.gov[^\"><]*/seq-\d+'
            newarray = []
            for string in returnarray:
                try:
                    base = re.findall(urlRegEx, string)[0]
                    newcore = ' <a href = "' + base + preface + joiner.join(self.actualWords) + '"> search inside </a>'
                    string = re.sub("^<td>", "", string)
                    string = re.sub("</td>$", "", string)
                    string = string+newcore
                except IndexError:
                    pass
                newarray.append(string)
        # Arxiv is messier, requiring a whole different URL interface: http://search.arxiv.org:8081/paper.jsp?r=1204.3352&qs=netwokr
        else:
            newarray = returnarray
        return newarray
    
    def execute(self):
        # This performs the query using the method specified in the passed parameters.
        if self.method == "Nothing":
            pass
        else:
            value = getattr(self, self.method)()
            return value

class databaseSchema(object):
    """
    This class stores information about the database setup that is used to optimize query creation query
    and so that queries know what tables to include.
    It's broken off like this because it might be usefully wrapped around some of 
    the backend features,
    because it shouldn't be run multiple times in a single query (that spawns two instances of itself),
    as was happening before.

    It's closely related to some of the classes around variables and
    variableSets in the Bookworm Creation scripts,
    but is kept separate for now: that allows a bit more flexibility, 
    but is probaby a Bad Thing in the long run.
    """

    def __init__(self, db):
        self.db = db
        self.cursor=db.cursor
        # has of what table each variable is in
        self.tableToLookIn = {}
        
        # hash of what the root variable for each search term is (eg,
        # 'author_birth' might be crosswalked to 'authorid' in the
        # main catalog.)
        self.anchorFields = {}

        # aliases: a hash showing internal identifications codes that
        # dramatically speed up query time, but which shouldn't be
        # exposed.  So you can run a search for "state," say, and the
        # database will group on a 50-element integer code instead of
        # a VARCHAR that has to be long enough to support
        # "Massachusetts" and "North Carolina."  A couple are
        # hard-coded in, but most are derived by looking for fields
        # that end in the suffix "__id" later.

        # The aliases starts with a dummy alias for fully grouped queries.
        self.aliases = {}
        self.newStyle(db)


    def newStyle(self, db):
        
        self.tableToLookIn['bookid'] = self.fallback_table('fastcat')
        self.tableToLookIn['filename'] = self.fallback_table('fastcat')
        ff = self.fallback_table('fastcat')
        self.anchorFields[ff] = ff
        
        self.tableToLookIn['wordid'] = self.fallback_table('wordsheap')
        self.tableToLookIn['word'] = self.fallback_table('wordsheap')

        ww = self.fallback_table('wordsheap')
        self.anchorFields[ww] = ww
        

        tablenames = dict()
        tableDepends = dict()
        q = "SELECT dbname,alias,tablename,dependsOn FROM masterVariableTable JOIN masterTableTable USING (tablename);"
        logging.debug(q)
        db.cursor.execute(q)
        
        for row in db.cursor.fetchall():
            (dbname, alias, tablename, dependsOn) = row
            tablename = self.fallback_table(tablename)
            dependsOn = self.fallback_table(dependsOn)
            
            self.tableToLookIn[dbname] = tablename
            self.anchorFields[tablename] = dependsOn
            
            self.aliases[dbname] = alias

    def fallback_table(self,tabname):
        """
        Fall back to the saved versions if the memory tables are unpopulated.

        Use a cache first to avoid unnecessary queries, though the overhead shouldn't be much.
        """
        tab = tabname
        if tab.endswith("_"):
            return tab
        if tab in ["words","master_bookcounts","master_bigrams","catalog"]:
            return tab

        if not hasattr(self,"fallbacks_cache"):
            self.fallbacks_cache = {}
            
        if tabname in self.fallbacks_cache:
            return self.fallbacks_cache[tabname]
        
        q = "SELECT COUNT(*) FROM {}".format(tab)
        logging.debug(q)
        try:
            self.db.cursor.execute(q)
            length = self.db.cursor.fetchall()[0][0]
            if length==0:
                tab += "_"        
        except MySQLdb.ProgrammingError:
            tab += "_"
            
        self.fallbacks_cache[tabname] = tab
        
        return tab

    def tables_for_variables(self, variables, tables = []):
        tables = []

        for variable in variables:
            lookup_table = self.tableToLookIn[variable]
            if lookup_table in tables:
                continue
            tables.append(lookup_table)
            while True:
                anchor = self.fallback_table(self.anchorFields[lookup_table])
                if anchor in tables:
                    break
                else:
                    tables.append(anchor)
                lookup_table = anchor
                
        return tables

    

def where_from_hash(myhash, joiner=None, comp = " = ", escapeStrings=True, list_joiner = " OR "):
    whereterm = []
    # The general idea here is that we try to break everything in search_limits down to a list, and then create a whereterm on that joined by whatever the 'joiner' is ("AND" or "OR"), with the comparison as whatever comp is ("=",">=",etc.).
    # For more complicated bits, it gets all recursive until the bits are all in terms of list.
    if joiner is None:
        joiner = " AND "
    for key in list(myhash.keys()):
        values = myhash[key]
        if isinstance(values, (str, bytes)) or isinstance(values, int) or isinstance(values, float):
            # This is just human-being handling. You can pass a single value instead of a list if you like, and it will just convert it
            # to a list for you.
            values = [values]
        # Or queries are special, since the default is "AND". This toggles that around for a subportion.

        if key == "$or" or key == "$OR":
            local_set = []
            for comparison in values:
                local_set.append(where_from_hash(comparison, comp=comp))
            whereterm.append(" ( " + " OR ".join(local_set) + " )")
        elif key == '$and' or key == "$AND":
            for comparison in values:
                whereterm.append(where_from_hash(comparison, joiner=" AND ", comp=comp))                
        elif isinstance(values, dict):
            if joiner is None:
                joiner = " AND "
            # Certain function operators can use MySQL terms.
            # These are the only cases that a dict can be passed as a limitations
            operations = {"$gt":">", "$ne":"!=", "$lt":"<",
                          "$grep":" REGEXP ", "$gte":">=",
                          "$lte":"<=", "$eq":"="}
            
            for operation in list(values.keys()):
                if operation == "$ne":
                    # If you pass a lot of ne values, they must *all* be false.
                    subjoiner = " AND "
                else:
                    subjoiner = " OR "
                whereterm.append(where_from_hash({key:values[operation]}, comp=operations[operation], list_joiner=subjoiner))
        elif isinstance(values, list):
            # and this is where the magic actually happens:
            # the cases where the key is a string, and the target is a list.
            if isinstance(values[0], dict):
                # If it's a list of dicts, then there's one thing that happens.
                # Currently all types are assumed to be the same:
                # you couldn't pass in, say {"year":[{"$gte":1900}, 1898]} to
                # catch post-1898 years except for 1899. Not that you
                # should need to.
                for entry in values:
                    whereterm.append(where_from_hash(entry))
            else:
                # Note that about a third of the code is spent on escaping strings.
                if escapeStrings:
                    if isinstance(values[0], (str, bytes)):
                        quotesep = "'"
                    else:
                        quotesep = ""

                    def escape(value):
                        # NOTE: stringifying the escape from MySQL; hopefully doesn't break too much.                        
                        return str(MySQLdb.escape_string(to_unicode(value)), 'utf-8')
                else:
                    def escape(value):
                        return to_unicode(value)
                    quotesep = ""

                joined = list_joiner.join([" ({}{}{}{}{}) ".format(key, comp, quotesep, escape(value), quotesep) for value in values])
                whereterm.append(" ( {} ) ".format(joined))

    if len(whereterm) > 1:
        return "(" + joiner.join(whereterm) + ")"
    else:
        return whereterm[0]
    # This works pretty well, except that it requires very specific sorts of terms going in, I think.
