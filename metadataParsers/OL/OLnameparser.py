#!/usr/bin/python                                                                                                                                                                 

import json
import re
import copy
import codecs
import sys

sys.path.append("..")
sys.path.append("../includes/nameparser-0.2.3")

from parsingClasses import *
from nameparser import HumanName

authors = "../../../Downloads/Catinfo/ol_dump_authors_latest.txt"
authorFile = open(authors)

class authorLine:
    """
    This is created with a jsonString
    """
    def __init__(self,OLline):
        jsonString = OLline.split("\t")[4]
        self.hash = json.loads(jsonString)
        self.parseNames()
        self.parseDates()

    def parseDates(self):
        for date in ['birth_date','death_date']:
            try:
                self.hash[date] = parsingClasses.date(self.hash[date]).extract_year()
            except:
                self.hash[date] = ''

    def parseNames(self):
        try:
            self.name = HumanName(self.hash['name'])
            self.hash['first'] = self.name.first
            self.hash['last'] = self.name.last
        except KeyError or ValueError:
            #keyError gets thrown on not having a name field: valueError gets thrown when nameparser gets confused.
            self.hash['first'] = ''
            self.hash['last']  = ''
            
    def tabulate(self):
        output = []
        for variable in ['key','name','first','last','birth_date','death_date']:
            try:
                output.append(to_unicode(self.hash[variable]))
            except KeyError:
                output.append('')
        return('\t'.join(output).encode("UTF-8"))

if __name__=='__main__':
    output = open("../../../metadata/authors.txt",'w')
    for line in authorFile:
        try:
            myline = authorLine(line)
            output.write(myline.tabulate()+"\n")
        except:
            pass
