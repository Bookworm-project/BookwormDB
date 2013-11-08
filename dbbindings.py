#!/usr/bin/env python

#So we load in the terms that allow the API implementation to happen for now.
execfile("APIimplementation.py")

import cgitb
cgitb.enable()

def headers(method):
    if method!="return_tsv":
        print "Content-type: text/html\n"
    elif method=="return_tsv":
        print "Content-type: text; charset=utf-8"
        print "Content-Disposition: filename=Bookworm-data.txt"
        print "Pragma: no-cache"
        print "Expires: 0\n"

try:        
    outfile = open("/var/log/presidio/log.txt",'a')
except IOError:
    outfile = open("/dev/null","a")
    #It doesn't have to log results anymore


form = cgi.FieldStorage()

if len(form) > 0: #(Use CGI input if it's there:)
    JSONinput = form["queryTerms"].value
    outfile.write(JSONinput)
    outfile.write("\n")
    output = open("/tmp/err",'w'); output.write(json.__file__)
    data = json.loads(JSONinput)
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
    headers(method)

    #if somewhere else has already set a privileges level, then you can get higher ones here.
    try:
        privileges = priorPrivileges
    except:
        privileges = "basic"


    if privileges == "minimal":
        if len (data['groupings']) > 1:
            print "Too many groupings: please request an API key to complete this operation"
        for group in data['groupings']:
            pass
            #if group not in ['year','month','day']
    p = userqueries(data)

else: #(Use command line input otherwise--this shouldn't be necessary anymore except for testing)
  try:
      command = str(sys.argv[1])
      command = json.loads(command)
      print command
      p = userquery(command)
  except:
      raise

#This following would be better as a straight switch.

if method!='return_tsv' and method!='return_json' and method!='search_results' and method!='returnPossibleFields':
    result = p.execute()
    #This 'RESULT' bit NEEDS to go, but legacy code uses it heavily.
    print '===RESULT==='
    print json.dumps(result)

if method=='return_json' or method=='search_results' or method=='returnPossibleFields':
    result = p.execute()
    if isinstance(data['search_limits'],dict):
        print json.dumps(result[0])
    else:
        print json.dumps(result)

if method=="return_tsv":
    #Return_tsv can only give back a single file at a time.
    result = p.execute()[0]
    print result.encode('utf-8')
    print "\n"

"""
#This is no longer needed: export_tsv does the job much more cleanly.
if method=='export_data':
    result = p.execute()
    #build yearlist
    vals = [r['values'] for r in result]
    minyear = min([min(v.keys()) for v in vals])
    maxyear = max([max(v.keys()) for v in vals])
    data = [range(minyear,maxyear+1)]
    for v in vals:
        app=[]
        for y in data[0]:
            if y in v.keys():
                app.append(v[y])  
        data.append(app)
    print ",".join(["%d"%(x) for x in data[0]])
    print "\n".join([",".join(["%.5f"%(x) for x in d]) for d in data[1:]])
"""

