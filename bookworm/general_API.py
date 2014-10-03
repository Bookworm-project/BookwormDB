#!/usr/bin/python

import MySQLdb
from pandas import merge
from pandas.io.sql import read_sql
from SQLAPI import *
from copy import deepcopy
from collections import defaultdict
import ConfigParser
import os.path

#Some settings can be overridden here, if no where else.
prefs = dict()

def find_my_cnf():
    """
    The password will be looked for in these places.
    """
    
    for file in ["etc/bookworm/my.cnf","/etc/my.cnf","/etc/mysql/my.cnf"]:
        if os.path.exists(file):
            return file

class dbConnect(object):
    #This is a read-only account
    def __init__(self,prefs=prefs,database="federalist",host="localhost"):
        self.dbname = database

        #For back-compatibility:
        if "HOST" in prefs:
            host=prefs['HOST']

        self.db = MySQLdb.connect(host=host,
                                  db=database,
                                  read_default_file = find_my_cnf(),
                                  use_unicode='True',
                                  charset='utf8')

        self.cursor = self.db.cursor()

def calculateAggregates(df,parameters):

    """
    We only collect "WordCoun" and "TextCount" for each query,
    but there are a lot of cool things you can do with those:
    basic things like frequency, all the way up to TF-IDF.
    """
    parameters = set(parameters)
    
    if "WordsPerMillion" in parameters:
        df["WordsPerMillion"] = df["WordCount_x"].multiply(1000000)/df["WordCount_y"]
    if "WordCount" in parameters:
        df["WordCount"] = df["WordCount_x"]
    if "TotalWords" in parameters:
        df["TotalWords"] = df["WordCount_y"]
    if "SumWords" in parameters:
        df["SumWords"] = df["WordCount_y"] + df["WordCount_x"]
    if "WordsRatio" in parameters:
        df["WordsRatio"] = df["WordCount_x"]/df["WordCount_y"]

    if "TextPercent" in parameters:
        df.eval("TextPercent = 100*TextCount_x/TextCount_y")
    if "TextCount" in parameters:
        df["TextCount"] = df["TextCount_x"]
    if "TotalTexts" in parameters:
        df["TotalTexts"] = df["TextCount_y"]

    if "HitsPerBook" in parameters:
        df.eval("HitsPerMatch = WordCount_x/TextCount_x")
    if "TextLength" in parameters:
        df.eval("TextLength = WordCount_y/TextCount_y")

    if "TFIDF" in parameters:
        from numpy import log as log
        df.eval("TF = WordCount_x/WordCount_y")
        df["TFIDF"] = (df["WordCount_x"]/df["WordCount_y"])*log(df["TextCount_y"]/df['TextCount_x'])

    def DunningLog(df=df,a = "WordCount_x",b = "WordCount_y"):
        from numpy import log as log
        destination = "Dunning"
        if a=="WordCount_x":
            # Dunning comparisons should be to the sums if counting:
            c = sum(df[a])
            d = sum(df[b])
        if a=="TextCount_x":
            # The max count isn't necessarily the total number of books, but it's a decent proxy.
            c = max(df[a])
            d = max(df[b])
        expectedRate = (df[a] + df[b]).divide(c+d)
        E1 = c*expectedRate
        E2 = d*expectedRate
        diff1 = log(df[a].divide(E1))
        diff2 = log(df[b].divide(E2))
        df[destination] = 2*(df[a].multiply(diff1) + df[b].multiply(diff2))
        # A hack, but a useful one: encode the direction of the significance,
        # in the sign, so negative 
        difference = diff1<diff2
        df.ix[difference,destination] = -1*df.ix[difference,destination]
        return df[destination]

    if "Dunning" in parameters:
        df["Dunning"] = DunningLog(df,"WordCount_x","WordCount_y")
        
    if "DunningTexts" in parameters:
        df["DunningTexts"] = DunningLog(df,"TextCount_x","TextCount_y")

    return df
    
def intersectingNames(p1,p2,full=False):
    """
    The list of intersection column names between two DataFrame objects.

    'full' lets you specify that you want to include the count values:
    Otherwise, they're kept separate for convenience in merges.
    """
    exclude = set(['WordCount','TextCount'])
    names1 = set([column for column in p1.columns if column not in exclude])
    names2 = [column for column in p2.columns if column not in exclude]
    if full:
        return list(names1.union(names2))
    return list(names1.intersection(names2))

def base_count_types(list_of_final_count_types):
    """
    the final count types are calculated from some base types across both
    the local query and the superquery.
    """
    
    output = set()

    for count_name in list_of_final_count_types:
        if count_name in ["WordCount","WordsPerMillion","WordsRatio","TotalWords","SumWords","Dunning"]:
            output.add("WordCount")
        if count_name in ["TextCount","TextPercent","TextRatio","TotalTexts","SumTexts","DunningTexts"]:
            output.add("TextCount")
        if count_name in ["TextLength","HitsPerMatch","TFIDF"]:
            output.add("TextCount")
            output.add("WordCount")
        
            
    return list(output)

def is_a_wordcount_field(string):
    if string in ["unigram","bigram","word"]:
        return True
    return False

class APIcall(object):
    """
    This is the base class from which more specific classes for actual 
    methods can be dispatched.
    
    Without a "return_pandas_frame" method, it won't run.
    """
    def __init__(self,APIcall):
        """
        Initialized with a dictionary unJSONed from the API defintion.
        """
        self.query = APIcall
        self.idiot_proof_arrays()
        self.set_defaults()

    def set_defaults(self):
        query = self.query
        if not "search_limits" in query:
            self.query["search_limits"] = dict()
        if "unigram" in query["search_limits"]:
            #Hack: change somehow. You can't group on "word", just on "unigram"
            query["search_limits"]["word"] = query["search_limits"]["unigram"]
            del query["search_limits"]["unigram"]
            
    def idiot_proof_arrays(self):
        for element in ['counttype','groups']:
            try:
                if not isinstance(self.query[element],list):
                    self.query[element] = [self.query[element]]
            except KeyError:
                #It's OK if it's not there.
                pass

    def get_compare_limits(self):
        """
        The compare limits will try to 
        first be the string specified:
        if not that, then drop every term that begins with an asterisk:
        if not that, then drop the words term;
        if not that, then exactly the same as the search limits.
        """

        if "compare_limits" in self.query:
            return self.query['compare_limits']

        search_limits = self.query['search_limits']
        compare_limits = deepcopy(search_limits)

        asterisked = False
        for limit in search_limits.keys():
            if re.search(r'^\*',limit):
                search_limits[limit.replace('*','')] = search_limits[limit]
                del search_limits[limit]
                del compare_limits[limit]
                asterisked = True
        
        if asterisked:
            return compare_limits

        #Next, try deleting the word term.
            
        for word_term in search_limits.keys():
            if word_term in ['word','unigram','bigram']:
                del compare_limits[word_term]

        #Finally, whether it's deleted a word term or not, return it all.
        return compare_limits
        
    def data(self):
        if hasattr(self,"pandas_frame"):
            return self.pandas_frame
        else:
            self.pandas_frame = self.get_data_from_source()
            return self.pandas_frame
        
    def get_data_from_source(self):

        """
        This is a 

        Note that this method could be easily adapted to run on top of a Solr instance or
        something else, just by changing the bits in the middle where it handles storage_format.
        """

        call1 = deepcopy(self.query)

        #The individual calls need only the base counts: not "Percentage of Words," but just "WordCount" twice, and so forth
        call1['counttype'] = base_count_types(call1['counttype'])
        call2 = deepcopy(call1)

        call2['search_limits'] = self.get_compare_limits()

        #Drop out asterisks for that syntactic sugar.
        for limit in call1['search_limits'].keys():
            if re.search(r'^\*',limit):
                call1['search_limits'][limit.replace('*','')] = call1['search_limits'][limit]
                del call1['search_limits'][limit]

        for group in self.query['groups']:
            if re.search(r'^\*',group):
                replacement = group.replace("*","")
                call1['groups'].remove(group)
                call1['groups'].append(replacement)
                self.query['groups'].remove(group)
                self.query['groups'].append(replacement)
                call2['groups'].remove(group)

        #Special case: unigram groupings are dropped if they're not explicitly limited
        #if "unigram" not in call2['search_limits']:
        #    call2['groups'] = filter(lambda x: not x in ["unigram","bigram","word"],call2['groups'])

        """
        This could use any method other than pandas_SQL:
        You'd just need to name objects df1 and df2 as pandas dataframes 
        """
        df1 = self.generate_pandas_frame(call1)
        df2 = self.generate_pandas_frame(call2)
         
        intersections = intersectingNames(df1,df2)
        fullLabels = intersectingNames(df1,df2,full=True)
        
        """
        Would this merge be faster with indexes?
        """
        if len(intersections) > 0:
            merged = merge(df1,df2,on=intersections,how='outer')
        else:
            """
            Pandas doesn't seem to have a full, unkeyed merge, so I simulate it with a dummy.
            """
            df1['dummy_merge_variable'] = 1
            df2['dummy_merge_variable'] = 1
            merged = merge(df1,df2,on=["dummy_merge_variable"],how='outer')
            
        merged = merged.fillna(int(0))
        
        calculations = self.query['counttype']
    
        calcced = calculateAggregates(merged,calculations)
        calcced = calcced.fillna(int(0))
        
        final_DataFrame = calcced[self.query['groups'] + self.query['counttype']]

        return final_DataFrame

    def execute(self):
        method = self.query['method']

        
        if isinstance(self.query['search_limits'],list):
            if self.query['method'] not in ["json","return_json"]:
                self.query['search_limits'] = self.query['search_limits'][0]
            else:
                return self.multi_execute()
        
        if method=="return_json" or method=="json":
            frame = self.data()
            return self.return_json()

        if method=="return_tsv" or method=="tsv":
            frame = self.data()
            return frame.to_csv(sep="\t",encoding="utf8",index=False)

        if method=="return_pickle" or method=="DataFrame":
            frame = self.data()
            from cPickle import dumps as pickleDumps
            return pickleDumps(frame,protocol=-1)

        # Temporary catch-all pushes to the old methods:
        if method in ["returnPossibleFields","search_results","return_books"]:
            query = userquery(self.query)
            if method=="return_books":
                return query.execute()
            return json.dumps(query.execute())



    def multi_execute(self):
        """
        Queries may define several search limits in an array
        if they use the return_json method.
        """
        returnable = []
        for limits in self.query['search_limits']:
            child = deepcopy(self.query)
            child['search_limits'] = limits
            returnable.append(self.__class__(child).return_json(raw_python_object=True))

        return json.dumps(returnable)

    def return_json(self,raw_python_object=False):
        query = self.query
        data = self.data()
        
        def fixNumpyType(input):
            #This is, weirdly, an occasional problem but not a constant one.
            if str(input.dtype)=="int64":
                return int(input)
            else:
                return input
        
        #Define a recursive structure to hold the stuff.
        def tree():
            return defaultdict(tree)
        returnt = tree()
        
        for row in data.itertuples(index=False):
            row = list(row)
            destination = returnt
            if len(row)==len(query['counttype']):
                returnt = [fixNumpyType(num) for num in row]
            while len(row) > len(query['counttype']):
                key = row.pop(0)
                if len(row) == len(query['counttype']):
                    # Assign the elements.
                    destination[key] = row
                    break
                # This bit of the loop is where we descend the recursive dictionary.
                destination = destination[key]
        if raw_python_object:
            return returnt
        
        
        return json.dumps(returnt)

class SQLAPIcall(APIcall):
    """
    To make a new backend for the API, you just need to extend the base API call
    class like this.

    This one is comically short because all the real work is done in the userquery object.

    But the point is, you need to define a function "generate_pandas_frame"
    that accepts an API call and returns a pandas frame.

    But that API call is more limited than the general API; you only need to support "WordCount" and "TextCount"
    methods.
    """
    
    def generate_pandas_frame(self,call):
        """

        This is good example of the query that actually fetches the results.
        It creates some SQL, runs it, and returns it as a pandas DataFrame.
        
        The actual SQL production is handled by the userquery class, which uses more
        legacy code.

        """
        con=dbConnect(prefs,self.query['database'])
        q = userquery(call).query()
        if self.query['method']=="debug":
            print q
        df = read_sql(q, con.db)
        return df


