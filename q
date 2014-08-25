#!/usr/local/bin/python

import MySQLdb
import pandas
from pandas import DataFrame
from pandas.io.sql import read_sql
from APIimplementation import *

#Some temporary junk

general_prefs = dict()
general_prefs["default"] = {"host": "localhost", "database": "YourDatabaseNameHere"}
prefs = general_prefs["default"]
execfile("MetaWorm.py");prefs=general_prefs['default'];prefs['database'] = 'historydiss'; prefs['HOST'] = 'localhost'; prefs['read_default_file'] = "/etc/my.cnf";  

class dbConnect(object):
    #This is a read-only account
    def __init__(self,prefs):
        self.dbname = prefs['database']
        self.db = MySQLdb.connect(host=prefs['HOST'],read_default_file = prefs['read_default_file'],use_unicode='True',charset='utf8',db=prefs['database'])
        self.cursor = self.db.cursor()





def calculateAggregates(self,parameters):
    parameters = set(parameters)
    
    if "WordsPerMillion" in parameters:
        self.eval("WordsPerMillion = WordCount_x*1000000/WordCount_y")
    if "WordCount" in parameters:
        self.eval("WordCount = WordCount_x")
    if "TotalWords" in parameters:
        self.eval("TotalWords = WordCount_y")
    if "SumWords" in parameters:
        self.eval("SumWords = WordCount_y + WordCount_x")

    return self
    
def intersectingNames(p1,p2,full=False):
    exclude = set(['WordCount','TextCount'])
    names1 = set([column for column in p1.columns if column not in exclude])
    names2 = [column for column in p2.columns if column not in exclude]
    if full:
        return list(names1.union(names2))
    return list(names1.intersection(names2))


if __name__=="__main__":
    con = dbConnect(prefs)
    API = {"groups":["school"],"counttype":"Occurrences_per_Million_Words","words_collation":"Case_Sensitive","database":"historydiss","search_limits":[{"word":["America"],"year_year":{"$gte":1873,"$lte":2014}}]}


    q = userquery(API)
    ratioquery = q.ratio_query(materialize=False)
    q1 = q.mainquery
    q2 = q.supersetquery
    df1 = read_sql(q1, con.db)
    df2 = read_sql(q2, con.db)

    intersections = intersectingNames(df1,df2)
    fullLabels = intersectingNames(df1,df2,full=True)
    
    merged = pandas.merge(df1,df2,on=intersections,how='outer')
    merged = merged.fillna(0)

    calculations = ["WordsPerMillion","TotalWords"]
    
    calcced = calculateAggregates(merged,calculations)

    victory = calcced[fullLabels + calculations]
    
