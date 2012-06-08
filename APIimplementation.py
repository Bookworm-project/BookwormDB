#!/usr/bin/python

import sys
import json
import cgi
import re

class dbConnect():
    #This is a read-only account, but we should find a way not to expose it online if it becomes part of the GitHub.
    def __init__(self,read_default_file="~/.my.cnf",HOST='chaucer.fas.harvard.edu',database='LOC'):
        import MySQLdb
        self.db = MySQLdb.connect(host=HOST,read_default_file = read_default_file,use_unicode='True',charset='utf8',db=database)
        self.cursor = self.db.cursor()
        self.cursor.execute("SET storage_engine=MYISAM;")


# The basic object here is a userquery: it takes dictionary as input, as defined in the API, and returns a value 
# via the 'execute' function whose behavior 
# depends on the mode that is passed to it. Given the dictionary, it can return a number of objects.
# The "Search_limits" array in the passed dictionary determines how many elements it returns; this lets multiple queries be bundled together.
# Most functions describe a subquery that might be combined into one big query in various ways.

class userqueries():
    #This is a set of queries that are bound together.
    def __init__(self,outside_dictionary = {"counttype":"Percentage_of_Books","search_limits":[{"word":["polka dot"],"LCSH":["Fiction"]}]},db = dbConnect()):
        #coerce one-element dictionaries to an array.
        if 'search_limits' not in outside_dictionary.keys():
            outside_dictionary['search_limits'] = [{"word":[]}]
        if isinstance(outside_dictionary['search_limits'],dict):
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
    def __init__(self,outside_dictionary = {"counttype":"Percentage_of_Books","search_limits":{"word":["polka dot"],"LCSH":["Fiction"]}},db = dbConnect()):
        #print "Initializing object"
        self.db = db
        #Certain constructions require a DB connection already available, so we just start it here.
        self.outside_dictionary = outside_dictionary
        self.cursor = db.cursor
        #I'm now allowing 'search_limits' to either be a dictionary or an array of dictionaries: this makes the syntax cleaner on most queries,
        #while still allowing some more complicated ones.
        if isinstance(outside_dictionary['search_limits'],list):
            outside_dictionary['search_limits'] = outside_dictionary['search_limits'][0]
        self.defaults(outside_dictionary) #Take some defaults
        self.move_to_next_set_of_limits() #Queue up the first query in the list
        self.derive_variables() #Derive some useful variables that the query will use.
        
    def defaults(self,outside_dictionary):
        #these are default values;these are the only values that can be set in the query
            #search_limits is an array of dictionaries;
            #each one contains a set of limits that are mutually independent
            #The other limitations are universal for all the search limits being set.
        
        self.search_limits = outside_dictionary.setdefault('search_limits',[{"word":["polka dot"]}])
        self.time_limits = outside_dictionary.setdefault('time_limits',[0,10000000])
        self.time_measure = outside_dictionary.setdefault('time_measure','year')
        self.counttype = outside_dictionary.setdefault('counttype',"Occurrences_per_Million_Words")
        self.words_collation = outside_dictionary.setdefault('words_collation',"Case_Insensitive")
        self.index  = outside_dictionary.setdefault('index',0)
        #Ordinarily, the input should be an an array of groups that will both select and group by.
        #The joins may be screwed up by certain names that exist in multiple tables, so there's an option to do something like 
        #SELECT catalog.bookid as myid, because WHERE clauses on myid will work but GROUP BY clauses on catalog.bookid may not 
        #after a sufficiently large number of subqueries.
        self.groups = outside_dictionary.setdefault('groups',[self.time_measure])
        self.selections = ",".join(self.groups)
        self.groupings  = ",".join([re.sub(".* as","",group) for group in self.groups])
        #This smoothing code really ought to go somewhere else, since it doesn't quite fit into the whole API mentality and is 
        #more about the webpage.
        self.smoothingType = outside_dictionary.setdefault('smoothingType',"triangle")
        self.smoothingSpan = outside_dictionary.setdefault('smoothingSpan',3)
        self.method = outside_dictionary.setdefault('method',"Nothing")
        self.tablename = outside_dictionary.setdefault('tablename','master'+"_bookcounts as bookcounts")

    def derive_variables(self):
        #These are locally useful, and depend on the variables
        #For now, no ways to define the subset in the below query
        lookups = {"Case_Insensitive":'word',"case_insensitive":"word","Case_Sensitive":"casesens","Correct_Medial_s":'ffix',"All_Words_with_Same_Stem":"stem","Flagged":'wflag'}
        try:
            self.word_field = lookups[self.words_collation]
        except:
            print "Error: Word Collation of " + self.words_collation + " seems not to work"
        self.limits = self.search_limits
        #Treat empty constraints as nothing at all, not as full restrictions.
        for key in self.limits.keys():
            if self.limits[key] == []:
                del self.limits[key]
        self.create_catalog_table()
        self.make_catwhere()
        self.make_wordwheres()

    def create_catalog_table(self):
        self.catalog = 'catalog' #Can be replaced with a more complicated query.
        if 'LCSH' in self.limits.keys():
            self.catalog = """catalog JOIN LCSH USING (bookid)"""
        if 'hasword' in self.limits.keys():
            #This is the sort of code I should have written more of: it just generates a new API call to fill a small part of the code here:
            #(in this case, it merges the 'catalog' entry with a select query on the word in the 'haswords' field. Enough of this could really
            #shrink the codebase, I suspect.
            if self.limits['hasword'] == []:
                del self.limits['hasword']
                return
            inc = 0
            import copy
            words = self.outside_dictionary['search_limits']['hasword']
            for word in words:
                mydict = copy.deepcopy(self.outside_dictionary)
                mydict['search_limits'] = self.limits
                mydict['search_limits']['word'] = [word]
                mydict['groups'] = ['catalog.bookid as myid']
                mydict['search_limits']['hasword']=[]
                tempquery = userquery(mydict)
                bookids = tempquery.counts_query()
                self.catalog = self.catalog + "\nJOIN (" + bookids + ") as hasword"+str(inc) +  " ON hasword" + str(inc) + ".myid=catalog.bookid " 
                inc = inc+1

    def make_wordwheres(self):
        if 'word' in self.limits.keys():
            self.words_actually_searched = self.limits['word']
            if re.search(' ',self.limits['word'][0]):
                self.limits['word1'] = []
                self.limits['word2'] = []
                for word in self.limits['word']:
                    array = word.split(" ")
                    self.limits['word1'].append(array[0])
                    self.limits['word2'].append(array[1])
                del self.limits['word']
            else:
                lookups = {"Case_Insensitive":'word',"case_insensitive":"word","Case_Sensitive":"casesens","Correct_Medial_s":'ffix',"All_Words_with_Same_Stem":"stem","Flagged":'wflag'}
                self.word_field = lookups[self.words_collation]
            #We should probably just pass the words_field to use directly, but for now, we look it up to make the API more human_readable.
                self.make_wordwhere()
                if len(self.catwhere)>0:
                    self.countwhere      = self.catwhere + " AND " + self.wordwhere
                else:
                    self.countwhere      = self.wordwhere
                    


    def execute(self):
        #This performs the query using the method specified in the passed parameters.
        if self.method=="Nothing":
            pass
        else:
            return getattr(self,self.method)()
                    
    def move_to_next_set_of_limits(self):
        pass


    def make_catwhere(self):
        #Where terms that don't include the words table join. Presumes there will only be one catalog table.
        catlimits = dict()
        for key in self.limits.keys():
            if key not in ('word','word1','word2','hasword'):
                catlimits[key] = self.limits[key]
        if len(catlimits.keys()) > 0:
            self.catwhere = where_from_hash(catlimits)
        else:
            self.catwhere = "TRUE"

    def make_wordwhere(self):
        #Mostly deprecated, maybe still used in a place or two. (check for that?)
        self.wordwhere = where_from_hash({"wordlookup.casesens":self.limits['word']})
        self.wordstable = """
          (wordsheap as words JOIN 
            wordsheap AS wordlookup 
            ON (words.%(word_field)s=wordlookup.%(word_field)s) )""" % self.__dict__
        silent = self.cursor.execute("SELECT words.word FROM %(wordstable)s WHERE %(wordwhere)s" % self.__dict__)
        values = self.cursor.fetchall()
        self.words_actually_searched = [value[0] for value in values]

    def return_wordstable(self, words = ['polka dot'], pos=1):
        #This returns an SQL sequence suitable for querying or, probably, joining, that gives a words table only as long as the words that are
        #listed in the query; it works with different word fields
        #The pos value specifies a number to go after the table names, so that we can have more than one table in the join.
        self.lookupname = "lookup" + str(pos)
        self.wordsname  = "words" + str(pos)
        if len(words) > 0:
            self.wordwhere = where_from_hash({self.lookupname + ".casesens":words})
            self.wordstable = """
            wordsheap as %(wordsname)s JOIN 
            wordsheap AS %(lookupname)s 
            ON ( %(wordsname)s.%(word_field)s=%(lookupname)s.%(word_field)s 
            AND  %(wordwhere)s   )  """ % self.__dict__ 
        else:
            #We want to have some words returned even if _none_ are the query so that they can be selected. Having all the joins doesn't allow that,
            #because in certain cases (merging by stems, eg) it would have multiple rows returned for a single word.
            self.wordstable = """
            wordsheap as %(wordsname)s """ % self.__dict__
        self.selectname = ""
        return self.wordstable

    def counts_query(self,countname='count'):
        self.countname=countname
        bookoperation = {"Occurrences_per_Million_Words":"sum(count)","Raw_Counts":"sum(count)","Percentage_of_Books":"count(DISTINCT catalog.bookid)","Number_of_Books":"count(DISTINCT catalog.bookid)"}
        catoperation = {"Occurrences_per_Million_Words":"sum(nwords)","Raw_Counts":"sum(nwords)","Percentage_of_Books":"count(nwords)","Number_of_Books":"count(nwords)"}        
        self.operation = bookoperation[self.counttype]
        #Deduce the words tables we're joining against (this should ultimately be split into a new function)
        #This relies on a determination already having been made about whether this is a unigram or bigram search; that's reflected in the keys passed.
        if re.search("word\d",','.join(self.limits.keys())) or re.search("words2",self.selections):
            self.main = '''
                 JOIN
                 master_bigrams as main
                 ON (catalog.bookid=main.bookid)
                 '''
            self.wordstable1 = self.return_wordstable(words = self.limits.setdefault('word1',[]),pos = 1)
            self.wordstable2 = self.return_wordstable(words = self.limits.setdefault('word2',[]),pos = 2)
            self.wordstables = """
                JOIN ( %(wordstable2)s )
                 ON (main.word2 = words2.wordid )
                JOIN 
                 ( %(wordstable1)s )
                 ON (main.word1 = words1.wordid )""" % self.__dict__
        elif re.search("word",','.join(self.limits.keys())) or re.search("word",self.selections):
            self.main = '''
                JOIN
                 master_bookcounts as main
                 ON (catalog.bookid=main.bookid)'''
            self.tablename = 'master_bookcounts'
            self.wordstable1 = self.return_wordstable(words=self.limits.setdefault('word',[]),pos=1)
            self.wordstables = """
              JOIN ( %(wordstable1)s )  ON (main.wordid = words1.wordid)
             """ % self.__dict__
        #Have _no_ words table if no words searched for or grouped by; instead just use nwords
        else:
            self.main = " "
            self.operation = catoperation[self.counttype]            
            self.wordstables = " "
        countsQuery = """
            SELECT
                %(selections)s,
                %(operation)s as %(countname)s
            FROM 
                %(catalog)s
                %(main)s
                %(wordstables)s 
            WHERE
                 %(catwhere)s
            GROUP BY 
                %(groupings)s
        """ % self.__dict__
        return countsQuery
    
    def ratio_query(self):
        finalcountcommands = {"Occurrences_per_Million_Words":"IFNULL(count,0)*1000000/total","Raw_Counts":"IFNULL(count,0)","Percentage_of_Books":"IFNULL(count,0)*100/total","Number_of_Books":"IFNULL(count,0)"}
        self.mainquery    = self.counts_query()
        self.countcommand = finalcountcommands[self.counttype]
        if True: #In the case that we're not using a superset of words; this can be changed later
            supersetGroups = [group for group in self.groups if not re.match('word',group)]
            self.selections= ",".join(supersetGroups)
            self.groupings = ",".join([re.sub(".* as","",group) for group in supersetGroups])
            self.finalgroupings = self.groupings
            for key in self.limits.keys():
                if re.match('word',key):
                    del self.limits[key]
        self.supersetquery= self.counts_query(countname='total')
        self.selections  = ",".join([re.sub(".* as","",group) for group in self.groups])
        self.groupings   = self.selections
        query = """
        SELECT
            %(selections)s,
            %(countcommand)s as value
        FROM 
            ( %(mainquery)s 
            ) as tmp 
            RIGHT JOIN 
             ( %(supersetquery)s ) as totaller
             USING (%(finalgroupings)s)
        GROUP BY %(groupings)s;""" % self.__dict__
        return query        

    def return_slug_data(self,force=False):
	temp_words = self.return_n_words(force = True)
	temp_counts = self.return_n_books(force = True)
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
        ##This returns a list of bookids in order by how well they match the sort terms.
        ## Using an IDF term will give better search results for case-sensitive searches, but is currently disabled
        ##
        LIMIT = int((100-percentile_to_return) * self.return_n_books()/100)
        countQuery = """
         SELECT
         bookid,
         sum(count*1000/nwords%(idfterm)s) as score
         FROM %(catalog)s LEFT JOIN %(tablename)s
         USING (bookid)
         WHERE %(whereterms)s
         GROUP BY bookid
 	 ORDER BY score DESC
         LIMIT %(LIMIT)s
         """ % {'groupings':self.groupings,'tablename':self.tablename,'catalog':self.catalog,'whereterms':self.countwhere,'idfterm':'','LIMIT':LIMIT}
        return countQuery
    
    def bibliography_query(self,limit = "100"):
        self.limit = limit
        self.idfterm = ""
        bibQuery = """
        SELECT author,title,editionid,ocaid
        FROM open_editions RIGHT JOIN (
        SELECT
        bookid
        FROM
        %(catalog)s LEFT JOIN %(tablename)s USING (bookid) JOIN %(wordstable)s
                 ON (bookcounts.wordid = words.wordid)
        WHERE %(wordwhere)s AND %(catwhere)s
        GROUP BY bookid ORDER BY sum(count*1000/nwords%(idfterm)s) DESC LIMIT %(limit)s
        ) as tmp USING(bookid)
        """ #% self.__dict__
        prep = self.counts_query()
        bibQuery = """SELECT author,title,editionid,ocaid                                                            
        FROM open_editions RIGHT JOIN (                                                                              
        SELECT                                                                                                       
        catalog.bookid                                                                                               
            FROM                                                                                                     
                %(catalog)s                                                                                          
                %(main)s                                                                                             
                %(wordstables)s                                                                                      
            WHERE                                                                                                    
                 %(catwhere)s                                                                                        
        GROUP BY bookid ORDER BY sum(count*1000/nwords%(idfterm)s) DESC LIMIT %(limit)s                              
        ) as tmp USING(bookid)""" % self.__dict__
        return bibQuery


        return bibQuery

    def return_books(self):
        #This preps up the display elements for a search.
        silent = self.cursor.execute(self.bibliography_query())
        returnarray = []
        for line in self.cursor.fetchall():
            bookinfo = dict()
            bookinfo["count"] = 0
            bookinfo["read_url"] = "http://www.archive.org/stream/" + line[3]
            bookinfo["cat_url"]  = "http://openlibrary.org/books/" + line[2]
            bookinfo["title"]    = line[1]
            bookinfo["author"]   = line[0]
            if bookinfo["author"] is None:
                bookinfo["author"] = "unknown"
            bookinfo["cover-image"] = "http://covers.openlibrary.org/b/olid/" + line[2] + "-S.jpg"
            returnarray.append(bookinfo)
        return json.dumps(returnarray)
        
    def return_query_values(self,query = "ratio_query"):
        values = []
        querytext = getattr(self,query)()
        if len(self.words_actually_searched) > 0:
            silent = self.cursor.execute(querytext)
            #Gets the results
            mydict = dict(self.cursor.fetchall())
            for key in mydict.keys():
                #Only return results inside the time limits
                if key >= self.time_limits[0] and key <= self.time_limits[1]:
                    mydict[key] = str(mydict[key])
                else:
                    del mydict[key]
            mydict = smooth_function(mydict,smooth_method = self.smoothingType,span = self.smoothingSpan)
        else:
            mydict = {0:"0"}
        #This is a good place to change some values.
        return {'index':self.index, 'Name':self.words_actually_searched,"values":mydict,'words_searched':self.words_actually_searched}

    def export_data(self,query1="ratio_query"):
        return self.return_query_values(query=query1)
    #############
    ##EXPERIMENTAL
    #############
    #These are functions Ben's just playing around for research; they may or may not find a home in bookworm. Even they get too involved, I'll split them out.

def where_from_hash(myhash,fieldsjoin = " AND ",termsjoin = " OR ",prefix = " (",suffix = ") "):
    myconditions = []
    for key in myhash.keys():
        values = myhash[key]
        if isinstance(values[0],basestring):
            quotesep = "'"
        else:
            quotesep = ""
        myconditions.append("(" + termsjoin.join([key + '=' + quotesep + str(term) + quotesep for term in values]) + ")")
    return prefix + fieldsjoin.join(myconditions) + suffix
    #This works pretty well, except that it requires very specific sorts of terms going in, I think.

def smooth_function(zinput,smooth_method = 'lowess',span = .05):
    if smooth_method not in ['lowess','triangle']:
        return zinput
    xarray = []
    yarray = []
    years = zinput.keys()
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
        smoothed = lowess(x,y,float(span),3)
        x = [int(p) for p in x]
        returnval = dict(zip(x,smoothed))
        return returnval
    if smooth_method == 'triangle':
        #print "starting triangle smoothing<br>"
        span = int(span) #Takes the floor--so no smoothing on a span < 1.
        returnval = zinput
        windowsize = span*2 + 1
        from numpy import average
        for key in zinput:
            surrounding = array(range(windowsize),dtype=float)
            weights = array(range(windowsize))
            for i in range(windowsize):
                key_dist = i - span #if span is 2, the zeroeth element is -2, the second element is 0 off, etc.
                workingon = int(key) + key_dist
                try:
                    surrounding[i] = float(zinput[workingon])
                    weights[i] = (span + 1 - abs(key_dist))**.5
                except:
                    surrounding[i] = 0
                    weights[i] = 0
            returnval[key] = round(average(surrounding,weights=weights),3)
        return returnval
    
def headers(method):
    # Martin put this in here to get the export function working; we should really figure out how to better
    # integrate it into the main structures.
    if method!="export_data":
        print "Content-type: text/html\n"
    elif method=='export_data':
        print "Content-type: application/vnd.ms-excel; name='excel'"
        print "Content-Disposition: filename=export.txt"
        print "Pragma: no-cache"
        print "Expires: 0\n"

#The idea is: this works by default by slurping up from the command line, but you could also load the functions in and run results on your own queries.
try:
    command = str(sys.argv[1])
    command = json.loads(command)
#Got to go before we let anything else happen.
    print command
    p = userqueries(command)
    result = p.execute()
    print '===RESULT==='
    print json.dumps(result)
except:
    pass

