#!/usr/bin/python

import sys
import json
import cgi
import re
import numpy #used for smoothing.
import copy

#These are here so we can support multiple databases with different naming schemes from a single API. A bit ugly to have here; could be part of configuration file somewhere else, I guess. there are 'fast' and 'full' tables for books and words;
#that's so memory tables can be used in certain cases for fast, hashed matching, but longer form data (like book titles)
#can be stored on disk. Different queries use different types of calls.
#Also, certain metadata fields are stored separately from the main catalog table; I list them manually here to avoid a database call to find out what they are,
#although the latter would be more elegant. The way to do that would be a database call
#of tables with two columns one of which is 'bookid', maybe, or something like that.
#(Or to add it as error handling when a query failed; only then check for missing files.

general_prefs = {"presidio":{"HOST":"melville.seas.harvard.edu","database":"presidio","fastcat":"fastcat","fullcat":"open_editions","fastword":"wordsheap","read_default_file":"/etc/mysql/my.cnf","fullword":"words","separateDataTables":["LCSH","gender"],"read_url_head":"http://www.archive.org/stream/"},"arxiv":{"HOST":"10.102.15.45","database":"arxiv","fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","fullword":"words","read_default_file":"/etc/mysql/my.cnf","separateDataTables":["genre","fastgenre","archive","subclass"],"read_url_head":"http://www.arxiv.org/abs/"},"jstor":{"HOST":"10.102.15.45","database":"jstor","fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","fullword":"words","read_default_file":"/etc/mysql/my.cnf","separateDataTables":["discipline"],"read_url_head":"http://www.arxiv.org/abs/"}, "politweets":{"HOST":"chaucer.fas.harvard.edu","database":"politweets","fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","fullword":"words","read_default_file":"/etc/mysql/my.cnf","separateDataTables":[],"read_url_head":"http://www.arxiv.org/abs/"},"LOC":{"HOST":"10.102.15.45","database":"LOC","fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","fullword":"words","read_default_file":"/etc/mysql/my.cnf","separateDataTables":[],"read_url_head":"http://www.arxiv.org/abs/"},"ChronAm":{"HOST":"10.102.15.45","database":"LOC","fastcat":"fastcat","fullcat":"catalog","fastword":"wordsheap","fullword":"words","read_default_file":"/etc/mysql/my.cnf","separateDataTables":[],"read_url_head":"http://www.arxiv.org/abs/"}}
#We define prefs to default to the Open Library set at first; later, it can do other things.

class dbConnect():
    #This is a read-only account
    def __init__(self,prefs = general_prefs['presidio']):
        import MySQLdb
        self.db = MySQLdb.connect(host=prefs['HOST'],read_default_file = prefs['read_default_file'],use_unicode='True',charset='utf8',db=prefs['database'])
        self.cursor = self.db.cursor()


# The basic object here is a userquery: it takes dictionary as input, as defined in the API, and returns a value 
# via the 'execute' function whose behavior 
# depends on the mode that is passed to it.
# Given the dictionary, it can return a number of objects.
# The "Search_limits" array in the passed dictionary determines how many elements it returns; this lets multiple queries be bundled together.
# Most functions describe a subquery that might be combined into one big query in various ways.

class userqueries():
    #This is a set of queries that are bound together; each element in search limits is iterated over, and we're done.
    def __init__(self,outside_dictionary = {"counttype":"Percentage_of_Books","search_limits":[{"word":["polka dot"],"LCSH":["Fiction"]}]},db = None):
        #coerce one-element dictionaries to an array.
        self.database = outside_dictionary.setdefault('database','presidio')
        prefs = general_prefs[self.database]
        self.prefs = prefs
        self.wordsheap = prefs['fastword']
        self.words = prefs['fullword']
        if 'search_limits' not in outside_dictionary.keys():
            outside_dictionary['search_limits'] = [{}]
        if isinstance(outside_dictionary['search_limits'],dict):
            #(allowing passing of just single dictionaries instead of arrays)
            outside_dictionary['search_limits'] = [outside_dictionary['search_limits']]
        self.returnval = []
        self.queryInstances = []
        for limits in outside_dictionary['search_limits']:
            mylimits = outside_dictionary
            mylimits['search_limits'] = limits
            localQuery = userquery(mylimits)
            self.queryInstances.append(localQuery)
            self.returnval.append(localQuery.execute())

    def execute(self):
        return self.returnval

class userquery():
    def __init__(self,outside_dictionary = {"counttype":"Percentage_of_Books","search_limits":{"word":["polka dot"],"LCSH":["Fiction"]}}):
        #Certain constructions require a DB connection already available, so we just start it here, or use the one passed to it.
        self.outside_dictionary = outside_dictionary
        self.prefs = general_prefs[outside_dictionary.setdefault('database','presidio')]
        self.db = dbConnect(self.prefs)
        self.cursor = self.db.cursor
        self.wordsheap = self.prefs['fastword']
        self.words = self.prefs['fullword']

        #I'm now allowing 'search_limits' to either be a dictionary or an array of dictionaries: 
        #this makes the syntax cleaner on most queries,
        #while still allowing some more complicated ones.
        if isinstance(outside_dictionary['search_limits'],list):
            outside_dictionary['search_limits'] = outside_dictionary['search_limits'][0]
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
        lookups = {"Case_Insensitive":'word',"case_insensitive":"word","Case_Sensitive":"casesens","Correct_Medial_s":'ffix',"All_Words_with_Same_Stem":"stem","Flagged":'wflag'}
        self.word_field = lookups[self.words_collation]

        self.groups = []
        try:
            groups = outside_dictionary['groups']
        except:
            groups = [outside_dictionary['time_measure']]

        if groups == []:
            groups = ["bookid is not null as In_Library"]
        if (len (groups) > 1):
            pass
            #self.groups = credentialCheckandClean(self.groups)
            #Define some sort of limitations here.
        for group in groups:
            group = group
            if group=="unigram" or group=="word":
                group = "words1." + self.word_field + " as unigram"
            if group=="bigram":
                group = "CONCAT (words1." + self.word_field + " ,' ' , words2." + self.word_field + ") as bigram"
            self.groups.append(group)

        self.selections = ",".join(self.groups)
        self.groupings  = ",".join([re.sub(".* as","",group) for group in self.groups])


        self.compare_dictionary = copy.deepcopy(self.outside_dictionary)
        if 'compare_limits' in self.outside_dictionary.keys():
            self.compare_dictionary['search_limits'] = outside_dictionary['compare_limits']
            del outside_dictionary['compare_limits']
        else: #if nothing specified, we compare the word to the corpus.
            for key in ['word','word1','word2','word3','word4','word5','unigram','bigram']:
                try:
                    del self.compare_dictionary['search_limits'][key]
                except:
                    pass
            for key in self.outside_dictionary['search_limits'].keys():
                if re.search('words?\d',key):
                    try:
                        del self.compare_dictionary['search_limits'][key]
                    except:
                        pass

        comparegroups = []
        #This is a little tricky behavior here--hopefully it works in all cases. It drops out word groupings.
        try:
            compareGroups = self.compare_dictionary['groups']
        except:
            compareGroups = [self.compare_dictionary['time_measure']]
        for group in compareGroups:
            if not re.match("words",group) and not re.match("[u]?[bn]igram",group):
                comparegroups.append(group)
        self.compare_dictionary['groups'] = comparegroups
        self.time_limits = outside_dictionary.setdefault('time_limits',[0,10000000])
        self.time_measure = outside_dictionary.setdefault('time_measure','year')
        self.counttype = outside_dictionary.setdefault('counttype',"Occurrences_per_Million_Words")

        self.index  = outside_dictionary.setdefault('index',0)
        #Ordinarily, the input should be an an array of groups that will both select and group by.
        #The joins may be screwed up by certain names that exist in multiple tables, so there's an option to do something like 
        #SELECT catalog.bookid as myid, because WHERE clauses on myid will work but GROUP BY clauses on catalog.bookid may not 
        #after a sufficiently large number of subqueries.
        #This smoothing code really ought to go somewhere else, since it doesn't quite fit into the whole API mentality and is 
        #more about the webpage.
        self.smoothingType = outside_dictionary.setdefault('smoothingType',"triangle")
        self.smoothingSpan = outside_dictionary.setdefault('smoothingSpan',3)
        self.method = outside_dictionary.setdefault('method',"Nothing")
        self.tablename = outside_dictionary.setdefault('tablename','master'+"_bookcounts as bookcounts")

    def derive_variables(self):
        #These are locally useful, and depend on the variables
        self.limits = self.search_limits
        #Treat empty constraints as nothing at all, not as full restrictions.
        for key in self.limits.keys():
            if self.limits[key] == []:
                del self.limits[key]
        self.create_catalog_table()
        self.make_catwhere()
        self.make_wordwheres()

    def create_catalog_table(self):
        self.catalog = self.prefs['fastcat'] #'catalog' #Can be replaced with a more complicated query.

        #Rather than just search for "LCSH", this should check query constraints against a list of tables, and join to them.
        #So if you query with a limit on LCSH, it joins the table "LCSH" to catalog; and then that table has one column, ALSO
        #called "LCSH", which is matched against. This allows a bookid to be a member of multiple catalogs.

        for limitation in self.prefs['separateDataTables']:
            #That re.sub thing is in here because sometimes I do queries that involve renaming.
            if limitation in [re.sub(" .*","",key) for key in self.limits.keys()] or limitation in [re.sub(" .*","",group) for group in self.groups]:
                self.catalog = self.catalog + """ JOIN """ + limitation + """ USING (bookid)"""

        #Here's a feature that's not yet fully implemented: it doesn't work quickly enough, probably because the joins involve a lot of jumping back and forth
        if 'hasword' in self.limits.keys():
            #This is the sort of code I should have written more of: 
            #it just generates a new API call to fill a small part of the code here:
            #(in this case, it merges the 'catalog' entry with a select query on 
            #the word in the 'haswords' field. Enough of this could really
            #shrink the codebase, I suspect. But for some reason, these joins end up being too slow to run.
            #I think that has to do with the temporary table being created; we need to figure out how
            #to allow direct access to wordsheap here without having the table aliases for the different versions of wordsheap
            #being used overlapping.
            if self.limits['hasword'] == []:
                del self.limits['hasword']
                return
            import copy
            #deepcopy lets us get a real copy of the dictionary 
            #that can be changed without affecting the old one.
            mydict = copy.deepcopy(self.outside_dictionary)
            mydict['search_limits'] = copy.deepcopy(self.limits)
            mydict['search_limits']['word'] = copy.deepcopy(mydict['search_limits']['hasword'])
            del mydict['search_limits']['hasword']
            tempquery = userquery(mydict)
            bookids = ''
            bookids = tempquery.counts_query()

            #If this is ever going to work, 'catalog' here should be some call to self.prefs['fastcat']
            bookids = re.sub("(?s).*catalog[^\.]?[^\.\n]*\n","\n",bookids)
            bookids = re.sub("(?s)WHERE.*","\n",bookids)
            bookids = re.sub("(words|lookup)([0-9])","has\\1\\2",bookids)
            bookids = re.sub("main","hasTable",bookids)
            self.catalog = self.catalog + bookids
            #del self.limits['hasword']

    def make_catwhere(self):
        #Where terms that don't include the words table join. Kept separate so that we can have subqueries only working on one half of the stack.
        catlimits = dict()
        for key in self.limits.keys():
            if key not in ('word','word1','word2','hasword') and not re.search("words\d",key):
                catlimits[key] = self.limits[key]
        if len(catlimits.keys()) > 0:
            self.catwhere = where_from_hash(catlimits)
        else:
            self.catwhere = "TRUE"

    def make_wordwheres(self):
        self.wordswhere = " TRUE "
        self.max_word_length = 0
        limits = []
        
        if 'word' in self.limits.keys():
            """
            This doesn't currently allow mixing of one and two word searches together in a logical way.
            It might be possible to just join on both the tables in MySQL--I'm not completely sure what would happen.
            But the philosophy has been to keep users from doing those searches as far as possible in any case.
            """
            for phrase in self.limits['word']:
                locallimits = dict()
                array = phrase.split(" ")
                n=1
                for word in array:
                    locallimits['words'+str(n) + "." + self.word_field] = word
                    self.max_word_length = max(self.max_word_length,n)
                    n = n+1
                limits.append(where_from_hash(locallimits))
                #XXX for backward compatability
                self.words_searched = phrase
            #del self.limits['word']
            self.wordswhere = '(' + ' OR '.join(limits) + ')'

        wordlimits = dict()

        limitlist = copy.deepcopy(self.limits.keys())

        for key in limitlist:
            if re.search("words\d",key):
                wordlimits[key] = self.limits[key]
                self.max_word_length = max(self.max_word_length,2)
                del self.limits[key]

        if len(wordlimits.keys()) > 0:
            self.wordswhere = where_from_hash(wordlimits)


#    def return_wordstableOld(self, words = ['polka dot'], pos=1):
#        #This returns an SQL sequence suitable for querying or, probably, joining, that gives a words table only as long as the words that are
#        #listed in the query; it works with different word fields
#        #The pos value specifies a number to go after the table names, so that we can have more than one table in the join. But those numbers
#        #have to be assigned elsewhere, so overlap is a danger if programmed poorly.
#        self.lookupname = "lookup" + str(pos)
#        self.wordsname  = "words" + str(pos)
#        if len(words) > 0:
#            self.wordwhere = where_from_hash({self.lookupname + ".casesens":words})
#            self.wordstable = """
#            %(wordsheap)s as %(wordsname)s JOIN 
#            %(wordsheap)s AS %(lookupname)s 
#            ON ( %(wordsname)s.%(word_field)s=%(lookupname)s.%(word_field)s 
#            AND  %(wordwhere)s   )  """ % self.__dict__ 
#        else:
#            #We want to have some words returned even if _none_ are the query so that they can be selected. Having all the joins doesn't allow that,
#            #because in certain cases (merging by stems, eg) it would have multiple rows returned for a single word.
#            self.wordstable = """
#            %(wordsheap)s as %(wordsname)s """ % self.__dict__
#        return self.wordstable

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
        elif self.max_word_length == 1 or re.search("word",self.selections):
            self.maintable = 'master_bookcounts'
            self.main = '''
                JOIN
                 master_bookcounts as main
                 ON (''' + self.prefs['fastcat'] + '''.bookid=main.bookid)'''
            self.tablename = 'master_bookcounts'
            self.wordstables = """
              JOIN ( %(wordsheap)s as words1)  ON (main.wordid = words1.wordid)
             """ % self.__dict__
        #Have _no_ words table if no words searched for or grouped by; instead just use nwords. This 
        #isn't strictly necessary, but means the API can be used for the slug-filling queries, and some others.
        else:
            self.main = " "
            self.operation = self.catoperation[self.counttype] #Why did I do this?    
            self.wordstables = " "
            self.wordswhere  = " TRUE " #Just a dummy thing. Shouldn't take any time, right?

    def counts_query(self,countname='count'):
        self.countname=countname
        self.bookoperation = {"Occurrences_per_Million_Words":"sum(main.count)","Raw_Counts":"sum(main.count)","Percentage_of_Books":"count(DISTINCT " + self.prefs['fastcat'] + ".bookid)","Number_of_Books":"count(DISTINCT "+ self.prefs['fastcat'] + ".bookid)"}
        self.catoperation = {"Occurrences_per_Million_Words":"sum(nwords)","Raw_Counts":"sum(nwords)","Percentage_of_Books":"count(nwords)","Number_of_Books":"count(nwords)"}        
        self.operation = self.bookoperation[self.counttype]
        self.build_wordstables()
        countsQuery = """
            SELECT
                %(selections)s,
                %(operation)s as %(countname)s
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
    
    def ratio_query(self):
        finalcountcommands = {"Occurrences_per_Million_Words":"IFNULL(count,0)*1000000/total","Raw_Counts":"IFNULL(count,0)","Percentage_of_Books":"IFNULL(count,0)*100/total","Number_of_Books":"IFNULL(count,0)"}
        self.countcommand = finalcountcommands[self.counttype]
        #if True: #In the case that we're not using a superset of words; this can be changed later
        #    supersetGroups = [group for group in self.groups if not re.match('word',group)]
        #    self.finalgroupings = self.groupings
        #    for key in self.limits.keys():
        #        if re.match('word',key):
        #            del self.limits[key]
        
        self.denominator =  userquery(outside_dictionary = self.compare_dictionary)
        self.supersetquery = self.denominator.counts_query(countname='total')

        if re.search("In_Library",self.denominator.selections):
            self.selections = self.selections + ", fastcat.bookid is not null as In_Library"

        #See above: In_Library is a dummy variable so that there's always something to join on.            
        self.mainquery    = self.counts_query()
        

        """
        We launch a whole new userquery instance here to build the denominator, based on the 'compare_dictionary' option (which in most 
        cases is the search_limits without the keys, see above.
        We then get the counts_query results out of that result.
        """
        

        self.totalMergeTerms = "USING (" + self.denominator.groupings + " ) "


        self.totalselections  = ",".join([re.sub(".* as","",group) for group in self.groups])

        query = """
        SELECT
            %(totalselections)s,
            %(countcommand)s as value
        FROM 
            ( %(mainquery)s 
            ) as tmp 
            RIGHT JOIN 
             ( %(supersetquery)s ) as totaller
             %(totalMergeTerms)s
        GROUP BY %(groupings)s;""" % self.__dict__
        return query        

    def return_slug_data(self,force=False):
        #Rather than understand this error, I'm just returning 0 if it fails.
        #Probably that's the right thing to do, though it may cause trouble later.
        #It's just a punishment for not later using a decent API call with "Raw_Counts" to extract these counts out, and relying on this ugly method.
        try:
            temp_words = self.return_n_words(force = True)
            temp_counts = self.return_n_books(force = True)
        except:
            temp_words = 0
            temp_counts = 0
        return [temp_counts,temp_words]    

    def return_n_books(self,force=False):
        if (not hasattr(self,'nbooks')) or force:
            query = "SELECT count(*) from " + self.catalog + " WHERE " + self.catwhere
            silent = self.cursor.execute(query)
            self.counts = int(self.cursor.fetchall()[0][0])
        return self.counts

    def return_n_words(self,force=False):
        if (not hasattr(self,'nwords')) or force:
            query = "SELECT sum(nwords) from " + self.catalog + " WHERE " + self.catwhere
            silent = self.cursor.execute(query)
            self.nwords = int(self.cursor.fetchall()[0][0])
        return self.nwords   

    def ranked_query(self,percentile_to_return = 99,addwhere = ""):
        #NOT CURRENTLY IN USE ANYWHERE--DELETE???
        ##This returns a list of bookids in order by how well they match the sort terms.
        ## Using an IDF term will give better search results for case-sensitive searches, but is currently disabled
        ##
        self.LIMIT = int((100-percentile_to_return) * self.return_n_books()/100)
        countQuery = """
         SELECT
         bookid,
         sum(main.count*1000/nwords%(idfterm)s) as score
         FROM %(catalog)s LEFT JOIN %(tablename)s
         USING (bookid)
         WHERE %(catwhere)s AND %(wordswhere)s
         GROUP BY bookid
 	 ORDER BY score DESC
         LIMIT %(LIMIT)s
         """ % self.__dict__
        return countQuery
    
    def bibliography_query(self,limit = "100"):
        #I'd like to redo this at some point so it could work as an API call.
        self.limit = limit
        self.ordertype = "sum(main.count*10000/nwords)"
        try:
            if self.outside_dictionary['ordertype'] == "random":
                if self.counttype=="Raw_Counts" or self.counttype=="Number_of_Books":
                    self.ordertype = "RAND()"
                else:
                    self.ordertype = "LOG(1-RAND())/sum(main.count)"
        except KeyError:
            pass

        #If IDF searching is enabled, we could add a term like '*IDF' here to overweight better selecting words
        #in the event of a multiple search.
        self.idfterm = ""
        prep = self.counts_query()

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
        #This preps up the display elements for a search.
        #All this needs to be rewritten.
        silent = self.cursor.execute(self.bibliography_query())
        returnarray = []
        for line in self.cursor.fetchall():
            returnarray.append(line[0])
        if not returnarray:
            returnarray.append("No results for this particular point: try again without smoothing")
        newerarray = self.custom_SearchString_additions(returnarray)
        return json.dumps(newerarray)

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
        db = self.outside_dictionary['database']
        if db in ('jstor','presidio','ChronAm','LOC'):
            self.getActualSearchedWords()
            if db=='jstor':
                joiner = "&searchText="
                preface = "?Search=yes&searchText="
                urlRegEx = "http://www.jstor.org/stable/\d+"
            if db=='presidio':
                joiner = "+"
                preface =  "#page/1/mode/2up/search/"
                urlRegEx = 'http://archive.org/stream/[^"# ><]*'
            if db in ('ChronAm','LOC'):
                preface = "/;words="
                joiner = "+"
                urlRegEx = 'http://chroniclingamerica.loc.gov[^\"><]*/seq-\d'
            newarray = []
            for string in returnarray:
                base = re.findall(urlRegEx,string)[0]
                newcore = ' <a href = "' +  base  + preface + joiner.join(self.actualWords) + '"> search inside </a>'
                string = re.sub("^<td>","",string)
                string = re.sub("</td>$","",string)
                string = string+newcore
                newarray.append(string)
        #Arxiv is messier, requiring a whole different URL interface: http://search.arxiv.org:8081/paper.jsp?r=1204.3352&qs=network
        return newarray

    def return_query_values(self,query = "ratio_query"):
        #The API returns a dictionary with years pointing to values.
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

    def arrayNest(self,array,returnt):
        #A recursive function to transform a list into a nested array
        if len(array)==2:
            try:
                returnt[array[0]] = float(array[1])
            except:
                returnt[array[0]] = array[1]
        else:
            try:
                returnt[array[0]] = self.arrayNest(array[1:len(array)],returnt[array[0]])
            except KeyError:
                returnt[array[0]] = self.arrayNest(array[1:len(array)],dict())
        return returnt

    def return_json(self,query='ratio_query'):
        if self.counttype=="Raw_Counts" or self.counttype=="Number_of_Books":
            query="counts_query"
        querytext = getattr(self,query)()
        silent = self.cursor.execute(querytext)
        names = [to_unicode(item[0]) for item in self.cursor.description]
        returnt = dict()
        lines = self.cursor.fetchall()
        for line in lines:
            returnt = self.arrayNest(line,returnt)
        return returnt

    def return_tsv(self,query = "ratio_query"):
        if self.counttype=="Raw_Counts" or self.counttype=="Number_of_Books":
            query="counts_query"
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
            return getattr(self,self.method)()


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

def where_from_hash(myhash,joiner=" AND ",comp = " = "):
    whereterm = []
    #The general idea here is that we try to break everything in search_limits down to a list, and then create a whereterm on that joined by whatever the 'joiner' is ("AND" or "OR"), with the comparison as whatever comp is ("=",">=",etc.).
    #For more complicated bits, it gets all recursive until the bits are in terms of list.
    for key in myhash.keys():
        values = myhash[key]
        if isinstance(values,basestring) or isinstance(values,int) or isinstance(values,float):
            #This is just error handling. You can pass a single value instead of a list if you like, and it will just convert it 
            #to a list for you.
            values = [values]
        #Or queries are special, since the default is "AND". This toggles that around for a subportion.
        if key=='$or' or key=="$OR":
            for comparison in values:
                whereterm.append(where_from_hash(comparison,joiner=" OR ",comp=comp))
                #The or doesn't get populated any farther down.
        elif isinstance(values,dict):
            #Certain function operators can use MySQL terms. These are the only cases that a dict can be passed as a limitations
            operations = {"$gt":">","$lt":"<","$grep":" REGEXP ","$gte":">=","$lte":"<=","$eq":"="}
            for operation in values.keys():
                whereterm.append(where_from_hash({key:values[operation]},comp=operations[operation],joiner=joiner))
        elif isinstance(values,list):
            #and this is where the magic actually happens
            if isinstance(values[0],dict):
                for entry in values:
                    whereterm.append(where_from_hash(entry))
            else:
                if isinstance(values[0],basestring):
                    quotesep="'"
                else:
                    quotesep = ""
                #Note the "OR" here. There's no way to pass in a query like "year=1876 AND year=1898" as currently set up.
                #Obviously that's no great loss, but there might be something I'm missing that would be.
                whereterm.append(" (" + " OR ".join([" (" + key+comp+quotesep+str(value)+quotesep+") " for value in values])+ ") ")
    return "(" + joiner.join(whereterm) + ")"
    #This works pretty well, except that it requires very specific sorts of terms going in, I think.



#I'd rather have all this smoothing stuff done at the client side, but currently it happens here.
def smooth_function(zinput,smooth_method = 'lowess',span = .05):
    if smooth_method not in ['lowess','triangle','rectangle']:
        return zinput
    xarray = []
    yarray = []
    years = zinput.keys()
    years.sort()
    for key in years:
        if zinput[key]!='None':
            xarray.append(float(key))
            yarray.append(float(zinput[key]))
    from numpy import array
    x = array(xarray)
    y = array(yarray)
    if smooth_method == 'lowess':
        #print "starting lowess smoothing<br>"
        from Bio.Statistics.lowess import lowess
        smoothed = lowess(x,y,float(span)/100,3)
        x = [int(p) for p in x]
        returnval = dict(zip(x,smoothed))
        return returnval
    if smooth_method == 'rectangle':
        from math import log
        #print "starting triangle smoothing<br>"
        span = int(span) #Takes the floor--so no smoothing on a span < 1.
        returnval = zinput
        windowsize = span*2 + 1
        from numpy import average
        for i in range(len(xarray)):
            surrounding = array(range(windowsize),dtype=float)
            weights = array(range(windowsize),dtype=float)
            for j in range(windowsize):
                key_dist = j - span #if span is 2, the zeroeth element is -2, the second element is 0 off, etc.
                workingon = i + key_dist
                if workingon >= 0 and workingon < len(xarray):
                    surrounding[j] = float(yarray[workingon])
                    weights[j] = 1
                else:
                    surrounding[j] = 0
                    weights[j] = 0
            returnval[xarray[i]] = round(average(surrounding,weights=weights),3)
        return returnval
    if smooth_method == 'triangle':
        from math import log
        #print "starting triangle smoothing<br>"
        span = int(span) #Takes the floor--so no smoothing on a span < 1.
        returnval = zinput
        windowsize = span*2 + 1
        from numpy import average
        for i in range(len(xarray)):
            surrounding = array(range(windowsize),dtype=float)
            weights = array(range(windowsize),dtype=float)
            for j in range(windowsize):
                key_dist = j - span #if span is 2, the zeroeth element is -2, the second element is 0 off, etc.
                workingon = i + key_dist
                if workingon >= 0 and workingon < len(xarray):
                    surrounding[j] = float(yarray[workingon])
                    #This isn't actually triangular smoothing: I dampen it by the logs, to keep the peaks from being too too big.
                    #The minimum is '2', since log(1) == 0, which is a nonesense weight.
                    weights[j] = log(span + 2 - abs(key_dist))
                else:
                    surrounding[j] = 0
                    weights[j] = 0
            
            returnval[xarray[i]] = round(average(surrounding,weights=weights),3)
        return returnval
    
#The idea is: this works by default by slurping up from the command line, but you could also load the functions in and run results on your own queries.
try:
    command = str(sys.argv[1])
    command = json.loads(command)
#Got to go before we let anything else happen.
    print command
    p = userqueries(command)
    result = p.execute()
    print json.dumps(result)
except:
    pass

