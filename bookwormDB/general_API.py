#!/usr/bin/python

from pandas import merge, Series, set_option, DataFrame
from pandas.io.sql import read_sql
from pyarrow import feather
from copy import deepcopy
from collections import defaultdict
from .duckdb import DuckQuery
from .bwExceptions import BookwormException
from .query_cache import Query_Cache
import re
import json
import logging
logger = logging.getLogger("bookworm")

import numpy as np
import csv
import io
import numpy as np
from urllib import request
from urllib import parse
import random

"""
The general API is some functions for working with pandas to calculate
bag-of-words summary statistics according to the API description.

It is not bound to any particular backend: instead, a subset of
methods in the API must be supported by subclassing APICall().

The only existing example of this is "SQLAPICall."
"""

# Some settings can be overridden here, if nowhere else.

prefs = dict()

def PMI(df, location, groups):
    """
    A simple PMI calculation. Arguments:

    'location': The field to calculate expected values for.
    'groups': The metadata to sum up over.

    """
    copy = df.copy()
    total = df[[location]].sum()
    copy['expected'] = total[0]
    for i in range(len(groups)):
        new_name = groups[i] + "__r"
        renamer = dict()
        renamer[location] = new_name
        etc = (df[[groups[i], location]].groupby(groups[i]).sum()/total).rename(renamer, axis="columns")
        copy = merge(copy, etc, left_on = groups[i], right_index = True)
        copy["expected"] = copy["expected"] * copy[new_name]
    return np.log(copy[location]/copy["expected"])

def rle(input):
    """
    Format a list as run-length encoding JSON.
    """
    output = [input[0]]
    for item in input[1:]:
        if isinstance(output[-1], list) and output[-1][1] == item:
            output[-1][0] += 1
        elif output[-1] == item:
            output[-1] = [2, item]
        else:
            output.append(item)
    return output

def DunningLog(df, a, b):
    from numpy import log as log
    destination = "Dunning"
    df[a] = df[a].replace(0, 0.5)
    df[b] = df[b].replace(0, 0.5)
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

class Aggregator(object):
    """
    We only collect "WordCount and "TextCount" for each query,
    but there are a multitude of things you can do with those:
    basic things like frequency, all the way up to TF-IDF.

    """
    def __init__(self, df, groups = None):
        self.df = df
        self.groups = groups

    def _aggregate(self, parameters):
        "Run the aggregation. Prefixed with an underscore so it doesn't show up in the dict."

        parameters = set(map(str, parameters))
        for parameter in parameters:
            getattr(self, parameter)()
        return self.df

    def WordCount(self):
        self.df["WordCount"] = self.df["WordCount_x"]

    def TextCount(self):
        self.df["TextCount"] = self.df["TextCount_x"]

    def WordsPerMillion(self):
        self.df["WordsPerMillion"] = (self.df["WordCount_x"].multiply(1000000)/
                                 self.df["WordCount_y"])
    def TotalWords(self):
        self.df["TotalWords"] = self.df["WordCount_y"]

    def SumWords(self):
        self.df["SumWords"] = self.df["WordCount_y"] + self.df["WordCount_x"]

    def WordsRatio(self):
        self.df["WordsRatio"] = self.df["WordCount_x"]/self.df["WordCount_y"]

    def TextPercent(self):
        self.df["TextPercent"] = 100*self.df["TextCount_x"].divide(self.df["TextCount_y"])

    def TextRatio(self):
        self.df["TextRatio"] = self.df["TextCount_x"]/self.df["TextCount_y"]

    def TotalTexts(self):
        self.df["TotalTexts"] = self.df["TextCount_y"]

    def SumTexts(self):
        self.df["SumTexts"] = self.df["TextCount_y"] + self.df["TextCount_x"]

    def HitsPerText(self):
        self.df["HitsPerText"] = self.df["WordCount_x"]/self.df["TextCount_x"]

    def TextLength(self):
        self.df["TextLength"] = self.df["WordCount_y"]/self.df["TextCount_y"]

    def PMI_words(self):
        self.df["PMI_words"] = PMI(self.df, "WordCount_x", self.groups)

    def PMI_texts(self):
        self.df["PMI_texts"] = PMI(self.df, "TextCount_x", self.groups)

    def TFIDF(self):
        from numpy import log as log
        self.df["TF"] = self.df["WordCount_x"]/self.df["WordCount_y"]
        self.df["TFIDF"] = self.df["TF"] * np.log(self.df["TextCount_y"]/self.df['TextCount_x'])

    def Dunning(self):
        self.df["Dunning"] = DunningLog(self.df, "WordCount_x", "WordCount_y")


    def DunningTexts(self):
        self.df["DunningTexts"] = DunningLog(self.df, "TextCount_x", "TextCount_y")

def rename(df, newkey):

    # Add "x" and "y" suffixed to the dataframes even when not explicitly needed.

    renamer = {}
    for k in ["WordCount", "TextCount"]:
        renamer[k] = k + "_" + newkey
    df.rename(index=str, columns=renamer, inplace = True)


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

def dates_to_iso(frame):
    
    for column in frame.columns:
        if "date" in str(frame[column].dtype):
            frame[column] = frame[column].apply(lambda x: x.isoformat())
        else:
            print(str(frame[column].dtype))
    return frame


def base_count_types(list_of_final_count_types):
    """
    the final count types are calculated from some base types across both
    the local query and the superquery.

    These are very not optimized--I should go through and cut out bad ones for more obscure count types.

    """

    subq = set()
    superq = set()

    for count_name in list_of_final_count_types:
        if count_name in ["WordCount", "WordsPerMillion", "WordsRatio",
                          "TotalWords", "SumWords", "Dunning", "PMI_words", "TextLength", "HitsPerMatch", "TFIDF"]:
            subq.add("WordCount")
            superq.add("WordCount")
        if count_name in ["TextCount", "TextPercent", "TextRatio",
                          "TotalTexts", "SumTexts", "DunningTexts", "PMI_texts",
                              "TextLength", "HitsPerMatch", "TFIDF"]:
            subq.add("TextCount")
            superq.add("TextCount")

    return [list(subq), list(superq)]


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
    def __init__(self, query):

        """
        Initialized with a dictionary unJSONed from the API defintion.
        """

        self.query = query
        self.idiot_proof_arrays()
        self.set_defaults()


    def clone(self, query):
        """
        Make a clone of the APIcall object.
        Used with multipart queries.

        Should be sure that query itself is deeply cloned.
        """
        return APIcall(query)

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
                if isinstance(self.query[element], str):
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
        for limit in list(search_limits.keys()):
            if re.search(r'^\*', limit):
                search_limits[limit.replace('*', '')] = search_limits[limit]
                del search_limits[limit]
                del compare_limits[limit]
                asterisked = True

        if asterisked:
            return compare_limits

        # Next, try deleting the word term.

        for word_term in list(search_limits.keys()):
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

    #@attr
    #data_frame(self):
    #    if self._pandas_frame is not None:
    #        return self.return_pandas_frame
            
        
    def validate_query(self):
        self.ensure_query_has_required_fields()

    def ensure_query_has_required_fields(self):

        required_fields = ['counttype', 'groups', 'database']
        if self.query['method'] in ['schema', 'search', 'returnPossibleFields']:
            required_fields = ['database']

        for field in required_fields:
            if field not in self.query:
                logger.error("Missing field: %s" % field)
                err = dict(message="Bad query. Missing \"%s\" field" % field,
                           code=400)
                raise BookwormException(err)

    def prepare_search_and_compare_queries(self):

        call1 = deepcopy(self.query)
        call2 = deepcopy(call1)
        call2['search_limits'] = self.get_compare_limits()

        # The individual calls need only the base counts: not "Percentage of
        # Words," but just "WordCount" twice, and so forth

        call1['counttype'], call2['counttype'] = base_count_types(self.query['counttype'])

        # Drop out asterisks for that syntactic sugar.
        for limit in list(call1['search_limits'].keys()):
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


    def get_data_from_source(self):
        """
        Retrieves data from the backend, and calculates totals.

        Note that this method could be easily adapted to run on top of a Solr
        instance or something else, just by changing the bits in the middle
        where it handles storage_format.
        """

        self.validate_query()

        if self.query['method'] in ['schema', 'search']:
            return self.generate_pandas_frame()

        self.prepare_search_and_compare_queries()

        """
        This could use any method other than pandas_SQL:
        You'd just need to redefine "generate_pandas_frame"
        """

        if not need_comparison_query(self.query['counttype']):
            df1 = self.generate_pandas_frame(self.call1)
#            rename(df1, "x")
            return df1[self.query['groups'] + self.query['counttype']]

        try:
            df1 = self.generate_pandas_frame(self.call1)
            rename(df1, "x")
            logger.debug(self.call2)
            df2 = self.generate_pandas_frame(self.call2)
            rename(df2, "y")

        except Exception as error:
            logging.exception("Database error")
            # One common error is putting in an inappropriate column
            try:
                column_search = re.search("Unknown column '(.+)' in 'field list'",str(error)).groups()
                if len(column_search) > 0:
                    return Series({"status": "error", "message": "No field in database entry matching desired key `{}`".format(column_search[0])})
                else:
                    return Series({"status": "error", "message": "Database error. "
                                   "Try checking field names.","code":str(error)})

            except:
                    return Series({"status": "error", "message": "Unknown error. ",
                                   "code":str(error)})

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
        gator = Aggregator(merged, self.query['groups'])
        calcced = gator._aggregate(calculations)
#        calcced = calculateAggregates(merged, calculations, self.query['groups'])

        calcced = calcced.fillna(int(0))

        final_DataFrame = (calcced[self.query['groups'] +
                           self.query['counttype']])

        return final_DataFrame

    def execute(self):

        method = self.query['method']
        fmt = self.query['format'] if 'format' in self.query else False
        if not 'method' in self.query:
            return "You must pass a method to the query."
        if method=="returnPossibleFields":
            self.query['method'] = "schema"
            method = "schema"

        version = 3
        try:
            # What to do with multiple search_limits

            if isinstance(self.query['search_limits'], list):
                if fmt == "json" or version >= 3:
                    frame = self.multi_execute(version = version)
                else:
                    # Only return first search limit if not return in json
                    self.query['search_limits'] = self.query['search_limits'][0]
            else:
                frame = self.data()

            if fmt == "json":

                val = dates_to_iso(frame).to_dict(orient = "records")
                return self._prepare_response(val, version = 2)

            if fmt == "csv":
                return frame.to_csv(encoding="utf8", index=False)

            if fmt == "tsv":
                return frame.to_csv(sep="\t", encoding="utf8", index=False)

            if fmt == "feather" or fmt == "feather_js":
                compression = "zstd"
                if fmt == "feather_js":
                    compression = "uncompressed"
                fout = io.BytesIO(b'')
                try:
                    feather.write_feather(frame, fout, compression = compression)
                except:
                    logger.warning("You need the pyarrow package installed to export as feather.")
                    raise
                fout.seek(0)
                return fout.read()

            if fmt == 'json_c':
                return self.return_rle_json(frame)

            if fmt == 'html':
                return self.html(frame)

            else:
                err = dict(status="error", code=200,
                            message="Only formats in ['csv', 'tsv', 'json', 'feather']"
                            " currently supported")
                return json.dumps(err)
        except BookwormException as e:
            # Error status codes are HTTP codes
            # http://www.restapitutorial.com/httpstatuscodes.html
            err = e.args[0]
            err['status'] = "error"
            return json.dumps(err)
        except Exception as ex:
            # General Uncaught error.
            logging.exception("{}".format(ex))
            logging.exception("Database error")
            return json.dumps({"status": "error", "message": "Database error. "
                            "Try checking field names."})

    def multi_execute(self, version=1):

        """
        Queries may define several search limits in an array
        if they use the return_json method.
        """

        if version <= 2:
            returnable = []
            for limits in self.query['search_limits']:
                child = deepcopy(self.query)
                child['search_limits'] = limits
                q = self.clone(child).return_json(raw_python_object=True,
                                                version=version)
                returnable.append(q)
            return self._prepare_response(returnable, version)

        if version >= 3:
            for i, limits in enumerate(self.query['search_limits']):
                child = deepcopy(self.query)
                child['search_limits'] = limits
                f = self.clone(child).data()
                f['Search'] = i
                if i == 0:
                    frame = f
                else:
                    frame = frame.append(f, ignore_index = True)
            return frame

    def html(self, data):
        """
        return an HTML table.
        """

        if isinstance(data, Series) and 'status' in data:
            # If data has a status, Bookworm is trying to send us an error
            return data.to_json()

        set_option('display.max_colwidth', -1)
        return data.to_html(escape = False, index = False)


    def return_rle_json(self, data):
        """
        Return data in column-oriented format with run-length encoding
        on duplicate values.
        """

        if isinstance(data, Series) and 'status' in data:
            # If data has a status, Bookworm is trying to send us an error
            return data.to_json()

        output = {'status':'success', 'data':{}}

        for k in data:
            series = data[k]
            output['data'][k] = rle(data[k].tolist())

        return json.dumps(output)


    def return_json(self, raw_python_object=False, version=1):
        '''
        Get JSON data for a single search_limit.

        version: 1 returns just the data, using method = return_json.
                 2 formats the response according to the JSend spec.
        '''
        query = self.query
        data = self.data()

        if isinstance(data, Series) and 'status' in data:
            # If data has a status, Bookworm is trying to send us an error
            return data.to_json()

        def fixNumpyType(input):
            # This is, weirdly, an occasional problem but not a constant one.
            if type(input) is np.int64:
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
                    try:
                        row = [
                            r if np.isfinite(row)
                        else None
                        for r in row
                        ]
                    except:
                        logger.warning(row)
                        pass
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

        return json.dumps(resp)


class oldSQLAPIcall(APIcall):
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

    def generate_pandas_frame(self, call = None):
        """

        This is good example of the query that actually fetches the results.
        It creates some SQL, runs it, and returns it as a pandas DataFrame.

        The actual SQL production is handled by the userquery class, which uses
        more legacy code.

        """

        if call is None:
            call = self.query

        con = DbConnect(prefs, self.query['database'])
        q = userquery(call).query()
        df = read_sql(q, con.db)
        return df

class MetaAPIcall(APIcall):
    def __init__(self, endpoints):
        self.endpoints = endpoints
        super().__init__(self)

    def connect(self, endpoint):
        # return some type of a connection.
        pass

    def generate_pandas_frame(self, call):
        if call is None:
            call = deepcopy(self.query)
            call['format'] = 'feather'
        for endpoint in self.endpoints:
            connection = self.connect(endpoint)
            d = connection.query(call)
        count_fields = []

        for field in ['WordCount', 'TextCount']:
            if field in call["counttype"]:
                count_fields.push(field)
        together = pd.concat(d)
        together[count_fields].sum()

class DuckDBCall(APIcall):
    """
    Fetches from DuckDB. Must create a connection before passing,
    to discourage on-the-fly creation which is slow.
    """

    def __init__(self, query, db):

        self.db = db
        super().__init__(query)

    def clone(self, query):
        """
        Make a clone of the object.
        Used with multipart queries.

        """
        return DuckDBCall(query, db = self.db)

    def generate_pandas_frame(self, call = None):
        """

        This is good example of the query that actually fetches the results.
        It creates some SQL, runs it, and returns it as a pandas DataFrame.

        The actual SQL production is handled by the userquery class, which uses
        more legacy code.

        """
        if call is None:
            call = self.query
        q = DuckQuery(call, db = self.db)
        if call['method'] == 'schema':
             m = q.databaseScheme.to_pandas()
             return m
        query = q.query()
        logger.warning("Preparing to execute {}".format(query))
        df = dates_to_iso(self.db.execute(query).df())
        logger.debug("Query retrieved")
        return df


def my_sort(something):
    if type(something) == list:
        return sorted(something)
    if type(something) == dict:
        keys = list(something.keys())
        keys.sort()
        output = {}
        for k in keys:
            output[k] = something[k]
        return output
    return something
    
def standardized_query(query: dict) -> dict:
    trimmed_call = {}
    needed_keys = [
        'search_limits',
        'compare_limits',
        'words_collation',
        'database',
        'method',
        'groups',
        'counttypes',
        ]
    needed_keys.sort()
    for k in needed_keys:
        try:
            trimmed_call[k] = my_sort(query[k])
        except KeyError:
            continue
    return trimmed_call


class ProxyAPI(APIcall):
    
    """
    Forward a request to a remote url.
    
    Can be useful if you want a proxy server with caching on one server which
    reaches out to a different server for uncached requests, or perhaps 
    if you want a single gateway for multiple different bookworms.
    
    """
    
    def __init__(self, query, endpoint):
        """
        Endpoint: A URL, like `http://localhost:10012`.
        """
        self.endpoint = endpoint
        super().__init__(query)
    
    def generate_pandas_frame(self, call = None) -> DataFrame:
        """
        Note--requires that the endpoint expose the new feather method.
        """
        
        if call is None:
            call = self.query
        call = deepcopy(call)
        call['format'] = 'feather'
        query_string = json.dumps(call)
        qstring = parse.quote(query_string)
        remote_url = f"{self.endpoint}/?{qstring}"
        buffer = io.BytesIO()
        connection = request.urlopen(remote_url)
        buffer.write(connection.read())
        try:
            return feather.read_feather(buffer)
        except:
            # TODO: re-throw bookworm errors with additional context.
            raise

class Caching_API(APIcall):
    def __init__(self, query: dict, cache: Query_Cache, fallback_api: APIcall, **kwargs):
        """
        cache: an existing Query_Cache method. These are expensive to create,
               so you don't get one generated by default.
               
        fallback_api: Must be initialized with a parent API class that also
                      inherits from APICall.
        
        kwargs: are passed to the fallback API.
        """
        self.cache = cache
        self.Fallback = fallback_api
        self.kwargs = kwargs
        super().__init__(query)
        
    def generate_pandas_frame(self, call = None) -> DataFrame:
        if call is None:
            call = self.query
            
        trimmed_call = standardized_query(call)
        try:
            return self.cache[trimmed_call]
        except FileNotFoundError:
            resolution = self.Fallback(call, **self.kwargs).generate_pandas_frame()
            self.cache[trimmed_call] = resolution
            if random.random() < .1:
                # Don't bother doing this every time.
                self.cache.trim_cache()
            return resolution