#!/usr/bin/python

from pandas import merge
from pandas import Series
from pandas.io.sql import read_sql
from copy import deepcopy
from collections import defaultdict
from SQLAPI import DbConnect
from SQLAPI import userquery
from bwExceptions import BookwormException
import re
import json
import logging

"""
The general API is some functions for working with pandas to calculate
bag-of-words summary statistics according to the API description.

It is not bound to any particular backend: instead, a subset of 
methods in the API must be supported by subclassing APICall().

The only existing example of this is "SQLAPICall."
"""

# Some settings can be overridden here, if nowhere else.

prefs = dict()

def calculateAggregates(df, parameters):

    """
    We only collect "WordCount and "TextCount" for each query,
    but there are a lot of cool things you can do with those:
    basic things like frequency, all the way up to TF-IDF.
    """
    parameters = map(str,parameters)
    parameters = set(parameters)
    
    if "WordCount" in parameters:
        df["WordCount"] = df["WordCount_x"]
    if "TextCount" in parameters:
        df["TextCount"] = df["TextCount_x"]
    if "WordsPerMillion" in parameters:
        df["WordsPerMillion"] = (df["WordCount_x"].multiply(1000000) /
                                 df["WordCount_y"])        
    if "TotalWords" in parameters:
        df["TotalWords"] = df["WordCount_y"]
    if "SumWords" in parameters:
        df["SumWords"] = df["WordCount_y"] + df["WordCount_x"]
    if "WordsRatio" in parameters:
        df["WordsRatio"] = df["WordCount_x"]/df["WordCount_y"]
        
    if "TextPercent" in parameters:
        df["TextPercent"] = 100*df["TextCount_x"].divide(df["TextCount_y"])
    if "TextRatio" in parameters:
        df["TextRatio"] = df["TextCount_x"]/df["TextCount_y"]        
    if "TotalTexts" in parameters:
        df["TotalTexts"] = df["TextCount_y"]
    if "SumTexts" in parameters:
        df["SumTexts"] = df["TextCount_y"] + df["TextCount_x"]
        
    if "HitsPerBook" in parameters:
        df["HitsPerMatch"] = df["WordCount_x"]/df["TextCount_x"]

    if "TextLength" in parameters:
        df["TextLength"] = df["WordCount_y"]/df["TextCount_y"]

    if "TFIDF" in parameters:
        from numpy import log as log
        df.eval("TF = WordCount_x/WordCount_y")
        df["TFIDF"] = ((df["WordCount_x"]/df["WordCount_y"]) *
                       log(df["TextCount_y"]/df['TextCount_x']))

    def DunningLog(df=df, a="WordCount_x", b="WordCount_y"):
        from numpy import log as log
        destination = "Dunning"
        df[a] = df[a].replace(0, 0.1)
        df[b] = df[b].replace(0, 0.1)
        if a == "WordCount_x":
            # Dunning comparisons should be to the sums if counting:
            c = sum(df[a])
            d = sum(df[b])
        if a == "TextCount_x":
            # The max count isn't necessarily the total number of books,
            # but it's a decent proxy.
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
        difference = diff1 < diff2
        df.ix[difference, destination] = -1*df.ix[difference, destination]
        return df[destination]

    if "Dunning" in parameters:
        df["Dunning"] = DunningLog(df, "WordCount_x", "WordCount_y")

    if "DunningTexts" in parameters:
        df["DunningTexts"] = DunningLog(df, "TextCount_x", "TextCount_y")

    return df


def intersectingNames(p1, p2, full=False):
    """
    The list of intersection column names between two DataFrame objects.

    'full' lets you specify that you want to include the count values:
    Otherwise, they're kept separate for convenience in merges.
    """
    exclude = set(['WordCount', 'TextCount'])
    names1 = set([column for column in p1.columns if column not in exclude])
    names2 = [column for column in p2.columns if column not in exclude]
    if full:
        return list(names1.union(names2))
    return list(names1.intersection(names2))


def need_comparison_query(count_types):
    """
    Do we not need a comparison query?
    """
    needing_fields = [c for c in count_types if not c in ["WordCount","TextCount"]]
    return len(needing_fields) != 0

def base_count_types(list_of_final_count_types):
    """
    the final count types are calculated from some base types across both
    the local query and the superquery.
    """

    output = set()

    for count_name in list_of_final_count_types:
        if count_name in ["WordCount", "WordsPerMillion", "WordsRatio",
                          "TotalWords", "SumWords", "Dunning"]:
            output.add("WordCount")
        if count_name in ["TextCount", "TextPercent", "TextRatio",
                          "TotalTexts", "SumTexts", "DunningTexts"]:
            output.add("TextCount")
        if count_name in ["TextLength", "HitsPerMatch", "TFIDF"]:
            output.add("TextCount")
            output.add("WordCount")

    return list(output)


def is_a_wordcount_field(string):
    if string in ["unigram", "bigram", "word"]:
        return True
    return False


class APIcall(object):
    """
    This is the base class from which more specific classes for actual
    methods can be dispatched.

    Without a "return_pandas_frame" method, it won't run.
    """
    def __init__(self, APIcall):
        """
        Initialized with a dictionary unJSONed from the API defintion.
        """
        self.query = APIcall
        self.idiot_proof_arrays()
        self.set_defaults()

    def set_defaults(self):
        query = self.query
        if "search_limits" not in query:
            self.query["search_limits"] = dict()
        if "unigram" in query["search_limits"]:
            # Hack: change somehow. You can't group on "word", just on
            # "unigram"
            query["search_limits"]["word"] = query["search_limits"]["unigram"]
            del query["search_limits"]["unigram"]

    def idiot_proof_arrays(self):
        for element in ['counttype', 'groups']:
            try:
                if not isinstance(self.query[element], list):
                    self.query[element] = [self.query[element]]
            except KeyError:
                # It's OK if it's not there.
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
            if re.search(r'^\*', limit):
                search_limits[limit.replace('*', '')] = search_limits[limit]
                del search_limits[limit]
                del compare_limits[limit]
                asterisked = True

        if asterisked:
            return compare_limits

        # Next, try deleting the word term.

        for word_term in search_limits.keys():
            if word_term in ['word', 'unigram', 'bigram']:
                del compare_limits[word_term]

        # Finally, whether it's deleted a word term or not, return it all.
        return compare_limits

    def data(self):
        if hasattr(self, "pandas_frame"):
            return self.pandas_frame
        else:
            self.pandas_frame = self.get_data_from_source()
            return self.pandas_frame


    def validate_query(self):
        self.ensure_query_has_required_fields()
        
    def ensure_query_has_required_fields(self):
        required_fields = ['counttype', 'groups']
        for field in required_fields:
            if field not in self.query:
                logging.error("Missing field: %s" % field)
                err = dict(message="Bad query. Missing \"%s\" field" % field,
                           code=400)
                raise BookwormException(err)


    def prepare_search_and_compare_queries(self):

        call1 = deepcopy(self.query)

        # The individual calls need only the base counts: not "Percentage of
        # Words," but just "WordCount" twice, and so forth
        call1['counttype'] = base_count_types(call1['counttype'])
        call2 = deepcopy(call1)

        call2['search_limits'] = self.get_compare_limits()

        # Drop out asterisks for that syntactic sugar.
        for limit in call1['search_limits'].keys():
            if re.search(r'^\*', limit):
                call1['search_limits'][limit.replace('*', '')] = \
                        call1['search_limits'][limit]
                del call1['search_limits'][limit]

        for n, group in enumerate(self.query['groups']):
            if re.search(r'^\*', group):
                replacement = group.replace("*", "")
                call1['groups'][n] = replacement
                self.query['groups'][n] = replacement
                call2['groups'].remove(group)

        self.call1 = call1
        self.call2 = call2
        # Special case: unigram groupings are dropped if they're not
        # explicitly limited
        # if "unigram" not in call2['search_limits']:
        #    call2['groups'] = filter(lambda x: x not in ["unigram", "bigram",
        #                                                 "word"],
        #                             call2['groups'])



    def get_data_from_source(self):
        """
        Retrieves data from the backend, and calculates totals.

        Note that this method could be easily adapted to run on top of a Solr
        instance or something else, just by changing the bits in the middle
        where it handles storage_format.
        """

        self.validate_query()
        self.prepare_search_and_compare_queries()
        
        """
        This could use any method other than pandas_SQL:
        You'd just need to redefine "generate_pandas_frame"
        """

        if not need_comparison_query(self.query['counttype']):
            df1 = self.generate_pandas_frame(self.call1)            
            return df1[self.query['groups'] + self.query['counttype']]

        try:
            df1 = self.generate_pandas_frame(self.call1)
            df2 = self.generate_pandas_frame(self.call2)
        except Exception as error:
            logging.exception("Database error")
            # One common error is putting in an inappropriate column
            column_search = re.search("Unknown column '(.+)' in 'field list'",str(error)).groups()
            if len(column_search) > 0:
                return Series({"status": "error", "message": "No field in database entry matching desired key `{}`".format(column_search[0])})
            else:
                return Series({"status": "error", "message": "Database error. "
                            "Try checking field names.","code":str(error)})

        
        
        intersections = intersectingNames(df1, df2)

        """
        Would this merge be faster with indexes?
        """
        if len(intersections) > 0:
            merged = merge(df1, df2, on=intersections, how='outer')
        else:
            merged = df1.join(df2, lsuffix='_x', rsuffix='_y')

        merged = merged.fillna(int(0))

        calculations = self.query['counttype']
        calcced = calculateAggregates(merged, calculations)
        
        calcced = calcced.fillna(int(0))

        final_DataFrame = (calcced[self.query['groups'] +
                           self.query['counttype']])

        return final_DataFrame

    def execute(self):

        method = self.query['method']
        fmt = self.query['format'] if 'format' in self.query else False
        version = 2 if method == 'data' else 1

        if version == 1:
            # What to do with multiple search_limits
            if isinstance(self.query['search_limits'], list):
                if method in ["json", "return_json"]:
                    return self.multi_execute(version=version)
                else:
                    # Only return first search limit if not return in json
                    self.query['search_limits'] = self.query['search_limits'][0]

            form = method[7:] if method[:6] == 'return' else method
            logging.warn("method == \"%s\" is deprecated. Use method=\"data\" "
                         "with format=\"%s\" instead." % (method, form))

            if method == "return_json" or method == "json":
                return self.return_json(version=1)

            elif method == "return_tsv" or method == "tsv":
                import csv
                frame = self.data()
                return frame.to_csv(sep="\t", encoding="utf8", index=False,
                                    quoting=csv.QUOTE_NONE, escapechar="\\")

            elif method == "return_pickle" or method == "DataFrame":
                frame = self.data()
                from cPickle import dumps as pickleDumps
                return pickleDumps(frame, protocol=-1)

        elif version == 2:
            try:
                # What to do with multiple search_limits
                if isinstance(self.query['search_limits'], list):
                    if fmt == "json":
                        return self.multi_execute(version=version)
                    else:
                        # Only return first search limit if not return in json
                        self.query['search_limits'] = self.query['search_limits'][0]

                if fmt == "json":
                    return self.return_json(version=2)
                else:
                    err = dict(status="error", code=200,
                               message="Only format=json currently supported")
                    return json.dumps(err)
            except BookwormException as e:
                # Error status codes are HTTP codes
                # http://www.restapitutorial.com/httpstatuscodes.html
                err = e.args[0]
                err['status'] = "error"
                return json.dumps(err)
            except:
                # General Uncaught error.
                logging.exception("Database error")
                return json.dumps({"status": "error", "message": "Database error. "
                               "Try checking field names."})

        # Temporary catch-all pushes to the old methods:
        if method in ["returnPossibleFields", "search_results",
                      "return_books"]:
                try:
                    query = userquery(self.query)
                    if method == "return_books":
                        return query.execute()
                    return json.dumps(query.execute())
                except Exception, e:
                    if len(str(e)) > 1 and e[1].startswith("Unknown database"):
                        return "No such bookworm {}".format(e[1].replace("Unknown database",""))
                except:
                    return "General error"

    def multi_execute(self, version=1):
        """
        Queries may define several search limits in an array
        if they use the return_json method.
        """
        returnable = []
        for limits in self.query['search_limits']:
            child = deepcopy(self.query)
            child['search_limits'] = limits
            q = self.__class__(child).return_json(raw_python_object=True,
                                                  version=version)
            returnable.append(q)

        return self._prepare_response(returnable, version)

    def return_json(self, raw_python_object=False, version=1):
        '''
        Get JSON data for a single search_limit.

        version: 1 returns just the data, using method=return_json.
                 2 formats the response according to the JSend spec.
        '''
        query = self.query
        data = self.data()

        if 'status' in data:
            # If data has a status, Bookworm is trying to send us an error
            return data.to_json()

        def fixNumpyType(input):
            # This is, weirdly, an occasional problem but not a constant one.
            if str(input.dtype) == "int64":
                return int(input)
            else:
                return input

        # Define a recursive structure to hold the stuff.
        def tree():
            return defaultdict(tree)
        returnt = tree()

        for row in data.itertuples(index=False):
            row = list(row)
            destination = returnt
            if len(row) == len(query['counttype']):
                returnt = [fixNumpyType(num) for num in row]
            while len(row) > len(query['counttype']):
                key = row.pop(0)
                if len(row) == len(query['counttype']):
                    # Assign the elements.
                    destination[key] = row
                    break
                # This bit of the loop is where we descend the recursive
                # dictionary.
                destination = destination[key]
        if raw_python_object:
            return returnt
        else:
            return self._prepare_response(returnt, version)

    def _prepare_response(self, data, version=1):
        if version == 1:
            resp = data
        elif version == 2:
            resp = dict(status="success", data=data)
        else:
            resp = dict(status="error",
                        data="Internal error: unknown response version")

        try:
            return json.dumps(resp, allow_nan=False)
        except ValueError:
            return json.dumps(resp)


class SQLAPIcall(APIcall):
    """
    To make a new backend for the API, you just need to extend the base API
    call class like this.

    This one is comically short because all the real work is done in the
    userquery object.

    But the point is, you need to define a function "generate_pandas_frame"
    that accepts an API call and returns a pandas frame.

    But that API call is more limited than the general API; you only need to
    support "WordCount" and "TextCount" methods.
    """

    def generate_pandas_frame(self, call):
        """

        This is good example of the query that actually fetches the results.
        It creates some SQL, runs it, and returns it as a pandas DataFrame.

        The actual SQL production is handled by the userquery class, which uses
        more legacy code.

        """
        con = DbConnect(prefs, self.query['database'])
        q = userquery(call).query()
        df = read_sql(q, con.db)
        return df
