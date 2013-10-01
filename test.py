#!/usr/bin/python

import MySQLdb
import cgi
import cgitb
import re

cgitb.enable()

class dbConnect():
  def __init__(self):
    self.db = MySQLdb.connect(host='localhost',use_unicode='True',charset='utf8',db='names',read_default_file="/etc/mysql/my.cnf")
    self.cursor=self.db.cursor()

class genderQuery:
  def __init__(self,name,prior=.5,db=dbConnect(),field='birth',year=1880,fuzziness=10):
    self.db=db
    self.name=re.sub("\W","",name) #prevents exploits
    self.prior=prior
    self.field=field
    self.firstYear=year-fuzziness
    self.lastYear=year+fuzziness

  def returnProb(self):
    query = """                                                                               SELECT gender,sum(count) as count FROM firstNames                                                            WHERE firstName="%(name)s" AND %(field)s > %(firstYear)s                                                           AND %(field)s < %(lastYear)s GROUP BY gender""" % self.__dict__
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

    return((vals['F']/total)/(vals['M']/total+vals['F']/total))

print "type:text/html\nhi"

if __name__=='main':                                                                  
  print "hi"
  form = cgi.FieldStorage()
  print genderQuery(form['name']).returnProb()
