#!/usr/bin/env python

#So we load in the terms that allow the API implementation to happen for now.
from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
import cgi
import cgitb
import json

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

    query = json.loads(JSONinput)
    # Print appropriate HTML headers
    headers(query['method'])
    # Set up the query.
    p = SQLAPIcall(query)
    #run the query.
    print p.execute() 

    return True


if __name__=="__main__":
    form = cgi.FieldStorage()

    #Still supporting two names for the passed parameter.
    try:
        JSONinput = form["queryTerms"].value
    except KeyError:
        JSONinput = form["query"].value

    main(JSONinput)


