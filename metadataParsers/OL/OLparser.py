#!/usr/bin/python

import json
import re
import copy
import codecs
import sys

sys.path.append("..")
sys.path.append("../includes/nameparser-0.2.3")

from parsingClasses import *
from nameparser import *

execfile("../parsingClasses.py")


#input    = "../../Downloads/Catinfo/ocaidbooks.txt"
#Our unique identifier
#input = "../../../Downloads/Catinfo/ocaidbooks.txt"
editions = "../../../Downloads/Catinfo/ol_dump_editions_latest.txt"

#Not necessary, but to make this faster I grep out only the files with 'ocaid' in them
editions = "../../../Downloads/Catinfo/editions.txt"
works = "../../../Downloads/Catinfo/ol_dump_works_latest.txt"
authors = "../../../Downloads/Catinfo/ol_dump_authors_latest.txt"

#OL stores variable in structures that have to be treated differently
singleVars = ["ocaid","title","publish_country","publish_date","key"]
multiVars  = ["lc_classifications","oclc_numbers","lccn","publish_places","publishers"]
hashVars   = ["languages","works","authors"]
derivedVars = ["lc0","lc1","lc2","year","author_birth","author_death","author","author_age"]

author_vars = ["name","birth_date","death_date"]
work_vars = ["subject_places","subject_people","subjects"]

catalog = open("../../../metadata/jsoncatalog.txt",'w')

class OLline(dict):
    #This is for processing an input line into a dictionary.
    def __init__(self,line):
        try:
            entry = json.loads(line.split("\t")[4])
            self.broken=0
        except:
            entry = dict()
            self.broken=1
        for key in entry.keys():
            self[key] = entry[key]
        try:
            self.etype = re.sub(".*/","",entry['type']['key'])
        except:
            pass

outsidedata = dict()

"""
for line in open(authors):
    entry = OLline(line)
    if entry.broken:
        continue
    for variable in author_vars:
        try:
            assignment = entry[variable]
            try: 
                outsidedata[entry['key']][variable] = assignment
            except:
                outsidedata[entry['key']] = dict()
                outsidedata[entry['key']][variable] = assignment
        except KeyError:
            pass

print "Author Data Loaded"

print "Loading Work Data..."
for line in open(works):
    entry = OLline(line)
    if entry.broken:
        continue
    for variable in work_vars:
        try:
            assignment = entry[variable]
            try: 
                outsidedata[entry['key']][variable] = assignment
            except:
                outsidedata[entry['key']] = dict()
                outsidedata[entry['key']][variable] = assignment
        except KeyError:
            pass

print "Work Data Loaded"
"""
entries = []

i=0 #counter for status updates

for line in open(editions):
    entry = OLline(line)

    if entry.broken:
        continue

    output = dict()
    localhash = {"multi":{},"single":{}}
        #Don't keep all the html junk about the type of key

    for singleVar in singleVars:
        try:
            output[singleVar] = entry[singleVar].encode("utf-8")
        except:
            pass

    for multiVar in multiVars:
        try:
            output[multiVar] = [string.encode('utf-8') for string in entry[multiVar]]
        except KeyError:
            pass

    for hashVar in hashVars:
        tmpresults = []
        for lochash in entry.setdefault(hashVar,[]):
            tmpresults.append(lochash['key'])
        output[hashVar] = tmpresults

    try:
        internetArchiveID = ocaid(output['ocaid'])
        output['filename'] = re.sub(".txt","",internetArchiveID.fileLocation())
    except:
        #if it doesn't have an ocaid field, give up and move to the next one.
        continue

    try:
        output['publish'] = date(output['publish_date']).extract_year()
    except KeyError:
        pass
        
    try:
        output['editionid'] = entry['key'].encode("utf-8")
        titlestring = "<em>" + output.get('title',"[No Title]") + "</em>"
        authorstring = output.get('author','[No author]')
        publishstring = "(" + str(output.get('year','undated')) + ")"
        output['searchstring'] = authorstring + ", " + titlestring + " " + publishstring + ' <a href="http://openlibrary.org' + output['editionid'] + '">more info</a> <a href="' + internetArchiveID.readerLocation() + '">read</a>'
    except:
        print output.keys()
        raise

    try:
        lcsubs = LCClass(entry['lc_classifications'][0]).split()
        for key in lcsubs.keys():
            output[key] = lcsubs[key]
    except KeyError:
        pass

    try:
        output['author'] = output['name']
    except KeyError:
        pass

    entries.append(output)
    #Periodically write out the results
    if len(entries)>=1000:
        for individual in entries:
            try:
                catalog.write(json.dumps(individual) + "\n")
            except UnicodeDecodeError:
                print "Unicode Error on "
                print individual

        print str(i*1000) + "\r"
        i = i+1
        entries = []
                 
for individual in entries:
    catalog.write(json.dumps(individual) + "\n")
