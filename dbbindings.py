#!/usr/bin/python

#So we load in the terms that allow the API implementation to happen for now. (Really, I'd like to actually run the API implementation, but this works for now; in fact, this is probably cleaner overall).
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

outfile = open("/var/log/presidio/log.txt",'a')
form = cgi.FieldStorage()

if len(form) > 0: #(Use CGI input if it's there:)
    JSONinput = form["queryTerms"].value
    outfile.write(JSONinput)
    outfile.write("\n")
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
    p = userqueries(data)

else: #(Use command line input otherwise--this shouldn't be necessary except for testing)
  try:
      command = str(sys.argv[1])
      command = json.loads(command)
      print command
      p = userquery(command)
  except:
      raise

#print p.method
if method!='return_tsv':
    result = p.execute()
    print '===RESULT==='
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

