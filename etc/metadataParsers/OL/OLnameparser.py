#!/usr/bin/python                                                                                                                                                                 

import json
import re
import copy
import codecs
import sys

sys.path.append("..")

import parsingClasses
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
        self.output = dict()
        
        self.parseNames()
        self.parseDates()
        self.parseOthers()

    def parseOthers(self):
        self.output['authors'] = self.hash['key']
        try:
            self.output['authorName'] = self.hash['name']
        except KeyError:
            pass

    def parseDates(self):
        for date in ['birth_date','death_date']:
            try:
                self.output['author_' + date] = parsingClasses.date(self.hash[date]).extract_year()
            except KeyError:
                pass

    def parseNames(self):
        try:
            self.name = HumanName(self.hash['name'])
            self.output['authorFirst'] = self.name.first
            self.output['authorLast'] = self.name.last
        except KeyError or ValueError:
            #keyError gets thrown on not having a name field: valueError gets thrown when nameparser gets confused.
            pass
            
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
    outputjson = open("../../../metadata/jsonauthors.txt",'w')
    for line in authorFile:
        try:
            myline = authorLine(line)
#            output.write(myline.tabulate()+"\n")
            outputjson.write(json.dumps(myline.output) + "\n")
        except:
            raise
