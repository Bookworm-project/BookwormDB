#!/usr/bin/env python
#!/usr/local/bin/python


#So we load in the terms that allow the API implementation to happen for now.
execfile("APIimplementation.py")
from datetime import datetime
import os
import cgitb
#import MySQLdb
cgitb.enable()

def headers(method):
    if method!="return_tsv":
        print "Content-type: text/html\n"
        userip = cgi.escape(os.environ["REMOTE_ADDR"])
        return userip
    elif method=="return_tsv":
        print "Content-type: text; charset=utf-8"
        print "Content-Disposition: filename=Bookworm-data.txt"
        print "Pragma: no-cache"
        print "Expires: 0\n"

form = cgi.FieldStorage()

if len(form) > 0: #(Use CGI input if it's there:)
    JSONinput = form["queryTerms"].value
    data = json.loads(JSONinput)
    try:
        usingSuccinctStyle = isinstance(data['search_limits'],dict)
    except:
        #If there are no search limits, it might be a returnPossibleFields query
        usingSuccinctStyle = True
    #For back-compatability, "method" can be defined in the json or as a separate part of the post.
    #Using the form-posting way of returning 'method' is deprecated.
    try:
        method = form["method"].value
        data['method'] = method
    except:
        try:
            method = data['method']
        except:
            raise
            pass
    p = userqueries(data)


else:
    #(Use command line input otherwise--this shouldn't be necessary anymore except for testing, so it's just a dummy query.) 
  data = {
    "database": "historydiss",
    "method": "return_json",
    "search_limits": {
        "word": ["America"]
    },
    "counttype": ["WordsPerMillion"],
    "groups": ["year_year"]
  }
  usingSuccinctStyle = True
  p = userqueries(data)
  method = "return_json"

headers(method)

if method!='return_tsv' and method!='return_json' and method!='search_results' and method!='returnPossibleFields':
    result = p.execute()
    #This 'RESULT' bit NEEDS to go, but legacy code uses it heavily.
    print '===RESULT==='
    print json.dumps(result)

if method=='return_json' or method=='search_results' or method=='returnPossibleFields':
    result = p.execute()
    if usingSuccinctStyle:
        print json.dumps(result[0])
    else:
        print json.dumps( result )

if method=="return_tsv":
    #Return_tsv can only give back a single file at a time.
    result = p.execute()[0]
    print result.encode('utf-8')
    print "\n"


def debug(string):
    """
    Makes it easier to debug through a web browser by handling the headers
    No calls should be permanently left in the code ever, or they will break things badly.
    """
    print headers('1')
    print "<br>"
    print string
    print "<br>"
