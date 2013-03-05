#!/usr/bin/python
"""
This is a set of methods to query a database (described elsewhere) for information about genders. It should be pretty quick.

Input is in the form of cgi fields. They can include:

1) a 'name' (a human first name: rare ones may not return results)
2) a 'prior' (a Bayesian prior belief, if you're working with groups that may be predominantly one gender)

"""
import MySQLdb
import cgi
import cgitb
import re
import json

cgitb.enable()

class dbConnect():
    def __init__(self):
        self.db = MySQLdb.connect(host='localhost',use_unicode='True',charset='utf8',db='names',read_default_file="/etc/mysql/my.cnf")
        self.cursor=self.db.cursor()

class genderQuery:
    def __init__(self,name,prior=.5,db=dbConnect(),field='birth',year="2008",fuzziness="10"):
        self.db=db
        self.name=re.sub("\W","",name) #prevents exploits
        self.prior=float(prior)
        self.field=field
        self.year = int(year)
        self.fuzziness = int(fuzziness)
        self.firstYear=self.year-self.fuzziness
        self.lastYear=self.year+self.fuzziness

    def returnProb(self):
        query = """
        SELECT gender,sum(count) as count FROM firstNames
        WHERE firstName="%(name)s" AND %(field)s > %(firstYear)s
             AND %(field)s < %(lastYear)s GROUP BY gender""" % self.__dict__
        #return(query)
        self.db.cursor.execute(query)
        vals = self.db.cursor.fetchall()
        vals = dict(vals)
        for letter in ["M","F"]:
            try:
                vals[letter]
            except:
                vals[letter] = 0
        
        total=sum([vals[key] for key in vals.keys()])

        if total > 20:
            return((vals['F']/total)/(vals['M']/total+vals['F']/total))
        if total < 20:
            return("NA")

if __name__=='__main__':
    form = cgi.FieldStorage()
    #args converts the form input in a dict we can pass straight to the query class.
    args = dict()
    for key in form.keys():
        args[key] = form[key].value
    if not ('name' in args.keys() or 'nameArray' in args.keys()):
        print "ERROR: Must include a 'name' field to search for"
    
    print "Content-type: text/html\n"
    print genderQuery(**args).returnProb()


