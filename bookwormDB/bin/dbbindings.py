#!/usr/bin/env python

# So we load in the terms that allow the API implementation to happen for now.
from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
import cgi
import cgitb
import json

cgitb.enable()


def headers(method, errorcode=False):

    print 'Access-Control-Allow-Origin: *'
    print 'Access-Control-Allow-Methods: GET, POST, PUT, OPTIONS'
    print 'Access-Control-Allow-Headers: Origin, Accept, Content-Type, ' \
          'X-Requested-With, X-CSRF-Token'

    if errorcode:
	print "Status: %d" % errorcode

    if method != "return_tsv":
        print "Content-type: text/html\n"

    elif method == "return_tsv":
        print "Content-type: text; charset=utf-8"
        print "Content-Disposition: filename=Bookworm-data.txt"
        print "Pragma: no-cache"
        print "Expires: 0\n"


def debug(string):
    """
    Makes it easier to debug through a web browser by handling the headers
    No calls should be permanently left in the code ever, or they will break
    things badly.
    """
    print headers('1')
    print "<br>"
    print string
    print "<br>"


def main(JSONinput):

    query = json.loads(JSONinput)
    # Set up the query.
    p = SQLAPIcall(query)

    # run the query.
    resp = p.execute()

    if query['method'] == 'data' and 'format' in query and query['format'] == 'json':
        try:
            resp = json.loads(resp)
        except:
            resp = dict(status="error", code=500,
                        message="Internal error: server did not return json")

        # Print appropriate HTML headers
        if 'status' in resp and resp['status'] == 'error':
            code = resp['code'] if 'code' in resp else 500
            headers(query['method'], errorcode=code)
        else:
            headers(query['method'])
        print json.dumps(resp)
    else:
        headers(query['method'])
        print resp

    return True


if __name__ == "__main__":
    form = cgi.FieldStorage()

    # Still supporting two names for the passed parameter.
    try:
        JSONinput = form["queryTerms"].value
    except KeyError:
        JSONinput = form["query"].value

    main(JSONinput)
