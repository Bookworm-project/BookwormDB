#!/usr/bin/env python


#So we load in the terms that allow the API implementation to happen for now.
from datetime import datetime
from bookworm.general_API import *
import os
import cgitb
#import MySQLdb
cgitb.enable()

def headers(method):
    if method!="return_tsv":
        print "Content-type: text/html\n"

    elif method=="return_tsv":
        print "Content-type: text; charset=utf-8"
        print "Content-Disposition: filename=Bookworm-data.txt"
        print "Pragma: no-cache"
        print "Expires: 0\n"

def debug(string):
    """
    Makes it easier to debug through a web browser by handling the headers
    No calls should be permanently left in the code ever, or they will break things badly.
    """
    print headers('1')
    print "<br>"
    print string
    print "<br>"



def main(JSONinput):

    query = JSONinput

    try:
        #Whether there are multiple search terms, as in the highcharts method.
        usingSuccinctStyle = isinstance(query['search_limits'],dict)
    except:
        #If there are no search limits, it might be a returnPossibleFields query
        usingSuccinctStyle = True

    headers(query['method'])

    p = SQLAPIcall(query)

    result = p.execute()
    print result

    return True

if __name__=="__main__":
    form = cgi.FieldStorage()

    try:
        JSONinput = form["queryTerms"].value
    except KeyError:
        JSONinput = form["query"].value

    main(json.loads(JSONinput))


