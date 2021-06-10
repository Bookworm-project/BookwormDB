#!/usr/local/bin/python

from .search_limits import Search_limits, where_from_hash
from .bwExceptions import BookwormException
from .DuckSchema import DuckSchema
import json
import re
import copy
import hashlib
import logging
logger = logging.getLogger("bookworm")

def fail_if_nonword_characters_in_columns(input):
    keys = all_keys(input)
    for key in keys:
        if re.search(r"[^A-Za-z_$*0-9]", key):
            logger.error("{} has nonword character".format(key))
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
    if query['method'] in ["schema", "search"]:
        # Queries below this only apply to "data"
        return
    for v in query['counttype']:
        if not v in ['WordCount', 'TextCount']:
            raise BookwormException({"code": 400, "message": 'Only "WordCount" and "TextCount"'
                                     ' counts are supported by the SQL api, but passed {}'.format(v)})

class DuckQuery(object):
    """
    The base class for a bookworm search.
    """
    def __init__(self, query_object = {}, db = None, databaseScheme = None):
        # Certain constructions require a DB connection already available, so we just start it here, or use the one passed to it.

        check_query(query_object)
        self.prefs = {}
        self.query_object = query_object
        self._db = db

        self.databaseScheme = databaseScheme
        if databaseScheme is None:
            self.databaseScheme = DuckSchema(self.db)
        self._wordswhere = None
        self.words = "words"
        self.defaults() # Take some defaults
        self.derive_variables() # Derive some useful variables that the query will use.
        self.set_operations()
        self._groups = None

    @property
    def db(self):
        if self._db is None:
            raise TypeError("Must supply database.")
        else:
            return self._db

    @property
    def method(self):
        return self.query_object['method']

    def defaults(self):
        # these are default values;these are the only values that can be set in the query
        # search_limits is an array of dictionaries;
        # each one contains a set of limits that are mutually independent
        # The other limitations are universal for all the search limits being set.

        query_object = self.query_object

        self.wordsTables = None
        # Set up a dictionary for the denominator of any fraction if it doesn't already exist:
        self.search_limits = query_object['search_limits']
        self.words_collation = query_object.get('words_collation', "Case_Sensitive")


        lookups = {
            "Case_Insensitive":'lowercase',
            'lowercase':'lowercase',
            'casesens':'word',
            "case_insensitive":"lowercase",
            "Case_Sensitive":"word",
            'stem':'stem'}

        self.word_field = lookups[self.words_collation]

    @property
    def groups(self):
        if self._groups:
            return self_groups
        self.groups = set()
        self.outerGroups = []
        self.finalMergeTables = set()

        try:
            groups = query_object['groups']
        except:
            groups = []

        for group in groups:

            # There's a special set of rules for how to handle unigram and bigrams
            multigramSearch = re.match("(unigram|bigram|trigram)([1-4])?", group)
        
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
                self.outerGroups.append(f"`{lookupTableName}`.`{self.word_field}` as {group}")
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
                        self.finalMergeTables.add(f' JOIN "{table}" USING ("{joinfield}")')
                    else:
                        self.groups.add('"' + group + '"')
                except KeyError:
                    self.groups.add('"' + group + '"')

        """
        There are the selections which can include table refs, and the groupings, which may not:
        and the final suffix to enable fast lookup
        """

        self.selections = ",".join(self.groups)
        self.groupings = ",".join([group for group in self.groups])

        self.joinSuffix = "" + " ".join(self.finalMergeTables)

        self.counttype = query_object['counttype']
        if isinstance(self.counttype, (str)):
            self.counttype = [self.counttype]

    @property
    def word_limits(self):
        if 'word' in self.limits:
            return True
        else:
            return False

    def derive_variables(self):
        # These are locally useful, and depend on the search limits put in.
        self.limits = self.search_limits

        # Treat empty constraints as nothing at all, not as restricting to the set of nothing.
        for key in list(self.limits.keys()):
            if self.limits[key] == []:
                del self.limits[key]
        self.set_operations()
#        self.create_catalog_table()

    @property
    def wordid_query(self):
        return self.wordswhere

        if self.wordswhere != " TRUE ":
            f = "SELECT wordid FROM { words } as words1 WHERE { wordswhere }".format(**self.__dict__)
            logger.debug("`" + self.wordswhere + "`")
            return " wordid IN ({})".format(f)
        else:
            return " TRUE "

    def make_group_query(self):
        aliases = []
        for g in self.query_object["groups"]:
            try:
                aliases.append(self.databaseScheme.aliases[g])
            except KeyError:
                aliases.append(g)

        if len(self.query_object["groups"]) > 0:
            return "GROUP BY {}".format(", ".join(self.query_object["groups"]))
        else:
            return " "

    def main_table(self):
        if self.gram_size() == 1:
            return '"unigram__ncid" as main'
        if self.gram_size() == 2:
            return '"word1_word2__ncid" as main'

    def full_query_tables(self):
        # Joins are needed to provide groups, but *not* to provide
        # provide evidence for wheres.

        # But if there's a group, there may also need to be an associated where.

        if self.word_limits:
            tables = [self.main_table()]
        else:
            tables = []
        cols = self.query_object['groups']
        s_keys = [k for k in pull_keys(self.limits) if not k in {"word", "unigram", "bigram", "trigram"}]
        
        enquoted = [f'"{tb}"' for tb in self.databaseScheme.tables_for_variables(cols + s_keys)]

        tabs = tables + enquoted
        if len(enquoted) == 0:
            tabs.append('"fastcat"')
        if self.using_nwords and not '"fastcat"' in tabs:
            tabs.append('"fastcat"')
        return tabs

    @property
    def query_tables(self):
        tables = self.full_query_tables()
        return " NATURAL JOIN ".join(tables)

    def base_query(self):
        return f"""
        SELECT {', '.join(self.set_operations() + self.query_object['groups'])}
        FROM {self.query_tables}
        WHERE
          {self._ncid_query()}
          AND
          {self.wordid_query}
          AND
          {self.catwhere}
        {self.make_group_query()}
        """

    @property
    def catalog_table(self):
        # NOT USED
        # self.catalog = self.prefs['fastcat'] # 'catalog' # Can be replaced with a more complicated query in the event of longer joins.

        """

        This should check query constraints against a list of tables, and
        join to them.  So if you query with a limit on LCSH, and LCSH
        is listed as being in a separate table, it joins the table
        "LCSH" to catalog; and then that table has one column, ALSO
        called "LCSH", which is matched against. This allows a _ncid
        to be a member of multiple catalogs.

        """

        self.relevantTables = set()

        databaseScheme = self.databaseScheme

        cols = self.needed_columns()

        cols = [c for c in cols if not c in {"word", "word1", "word2", "word3", "word4"}]
        if self.using_nwords:
            cols.append("nwords")
        print("\n\n", cols, "\n\n")
        self.relevantTables = self.databaseScheme.tables_for_variables(cols)

        self.catalog = " NATURAL JOIN ".join(self.relevantTables)
        return self.catalog

    @property
    def catwhere(self):
        # Where terms that don't include the words table join.
        catlimits = dict()

        for key in list(self.limits.keys()):
            if key not in ('word', 'word1', 'word2', 'word3', 'hasword') and not re.search("words[0-5]", key):
                catlimits[key] = self.limits[key]
        
        if len(list(catlimits.keys())) > 0:
            return where_from_hash(catlimits)
        else:
            return "TRUE"

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

    @property
    def wordswhere(self):
        if self._wordswhere:
            return self._wordswhere

        if not self.word_limits:
            self._wordswhere = " TRUE "
            return " TRUE "
        
        limits = []

        """
        This doesn't currently allow mixing of one and two word searches.
        """

        collation = self.query_object.get('words_collation', 'Case_Sensitive')
        word_field = "word"
        for phrase in self.limits['word']:
            locallimits = dict()
            array = phrase.split(" ")
            for n, word in enumerate(array):
                searchingFor = word
                if collation == "stem":
                    from nltk import PorterStemmer
                    searchingFor = PorterStemmer().stem_word(searchingFor)
                    word_field = "stem"
                if collation == "case_insensitive" or \
                    collation == "Case_Insensitive":
                    # That's a little joke. Get it?
                    searchingFor = searchingFor.lower()
                    print(searchingFor)
                    word_field = "lowercase"


                selectString = f"SELECT wordid FROM wordsheap WHERE \"{word_field}\" = '{searchingFor}'"
                logger.warning(selectString)
                self.db.execute(selectString)

                # Set the search key being used.
                search_key = "wordid"
                if self.gram_size() > 1:
                    # 1-indexed entries in the bigram tables.
                    search_key = f"word{n + 1}"

                for row in self.db.fetchall():
                    wordid = row[0]
                    try:
                        locallimits[search_key] += [wordid]
                    except KeyError:
                        locallimits[search_key] = [wordid]

            if len(locallimits) > 0:
                limits.append(where_from_hash(locallimits, comp = " = ", escapeStrings=False))


        self._wordswhere = "(" + ' OR '.join(limits) + ")"
        if limits == []:
            # In the case that nothing has been found, tell it explicitly to search for
            # a condition when nothing will be found.
            self._wordswhere = "_ncid = -1"

        wordlimits = dict()

        limitlist = copy.deepcopy(list(self.limits.keys()))

        for key in limitlist:
            if re.search("words[0-5]", key):
                wordlimits[key] = self.limits[key]
                self.max_word_length = max(self.max_word_length, 2)
                del self.limits[key]
        print(self._wordswhere)
        if len(list(wordlimits.keys())) > 0:
            self._wordswhere = where_from_hash(wordlimits)

        return self._wordswhere

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
                 bigrams_word1_word2 as main
            '''

            self.wordstables = """
            JOIN %(wordsheap)s as words1 ON (main.word1 = words1.wordid)
            JOIN %(wordsheap)s as words2 ON (main.word2 = words2.wordid) """ % self.__dict__

        # I use a regex here to do a blanket search for any sort of word limitations. That has some messy sideffects (make sure the 'hasword'
        # key has already been eliminated, for example!) but generally works.

        elif needsUnigrams:
            self.main = '''
            unigram__ncid as main
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
        self.using_nwords = False
        if with_words:
            if "TextCount" in self.query_object['counttype']:
                output.append("count(DISTINCT main._ncid) as 'TextCount'")
            if "WordCount" in self.query_object['counttype']:
                output.append("sum(main.count) as 'WordCount'")
        else:
            self.using_nwords = True
            if "WordCount" in self.query_object['counttype']:
                output.append("sum(nwords) as 'WordCount'")
            if "TextCount" in self.query_object['counttype']:
                output.append("count(DISTINCT _ncid) as 'TextCount'")

        return output

    def _ncid_query(self):

        q = f""" {self.catwhere} """
        logger.debug("'{}'".format(self.catwhere))
        if self.catwhere == "TRUE":
            self._ncid_where = " TRUE "
        else:
            self._ncid_where = q
        return self._ncid_where

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

        dicto = {
            'tables': self.make_join_query(),
            'ordertype': self.ordertype,
            'catwhere': self.catwhere,
            'limit': limit
        }

        dicto['_ncid_where'] = self._ncid_query()
        dicto['wordid_where'] = self.wordid_query

        bibQuery = """
        SELECT searchstring
        FROM catalog RIGHT JOIN (
        SELECT {fastcat}._ncid, {ordertype} as ordering
            FROM
               {tables}
            WHERE
               {_ncid_where} AND {wordid_where} and {catwhere}
        GROUP BY _ncid ORDER BY {ordertype} DESC LIMIT {limit}
        ) as tmp USING (_ncid) ORDER BY ordering DESC;
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
            logger.debug(q)
            self.db.execute(q)
            self.actualWords = [item[0] for item in self.db.fetchall()]
        else:
            raise TypeError("Suspiciously low word count")

def pull_keys(entry):
    val = []
    if isinstance(entry, list) and not isinstance(entry, (str, bytes)):
        for element in entry:
            val += pull_keys(element)
    elif isinstance(entry, dict):
        for k,v in entry.items():
            if k[0] != "$":
                val.append(k)
            else:
                val += pull_keys(v)
    else:
        return []

    return [key for key in val]
