#!/usr/bin/python

import json
import re
import copy
import codecs

input    = "../../Downloads/Catinfo/ocaidbooks.txt"
#Our unique identifier
input = "../../../Downloads/Catinfo/ocaidbooks.txt"
editions = "../../../Downloads/Catinfo/ocaidbooks.txt"
works = "../../../Downloads/Catinfo/ol_dump_works_latest.txt"
authors = "../../../Downloads/Catinfo/ol_dump_authors_latest.txt"

#OL stores variable in structures that have to be treated differently
singleVars = ["ocaid","title","publish_country","publish_date","key"]
multiVars  = ["lc_classifications","oclc_numbers","lccn","publish_places","publishers"]
hashVars   = ["languages","works","authors"]
derivedVars = ["lc0","lc1","lc2","year","author_birth","author_death","author","author_age"]

author_vars = ["birth_date","name","death_date"]
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

print "Loading author Data..."

outsidedata = dict()
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
entries = []


"""
**********************
BOOKWORM FUNCTION
**********************
"""
def lcPull(string):
    lcclass = string.encode("ascii",'replace')
    mymatch = re.match(r"^(?P<lc1>[A-Z]+) ?(?P<lc2>\d+)", lcclass)
    if mymatch:
        returnt = {'lc0':lcclass[0],'lc1':mymatch.group('lc1'),'lc2':mymatch.group('lc2')}
        return returnt
    else:
        return(dict())

def extract_year(string):
    years = re.findall("\d\d\d\d",string)
    if(years):
        return years[0]
    else:
        return "NULL"

def genderize(author):
    pass

i=1

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
            output[multiVar] = entry[multiVar]
        except:
            pass

    for hashVar in hashVars:
        tmpresults = []
        for lochash in entry.setdefault(hashVar,[]):
            tmpresults.append(lochash['key'])
        output[hashVar] = tmpresults

    for var in author_vars:
        try:
            output[var] = outsidedata[output['authors'][0]][var]
        except KeyError:
            pass

    for var in work_vars:
        try:
            output[var] = outsidedata[output['works'][0]][var]
        except KeyError:
            pass

    try:
        lcsubs = lcPull(entry['lc_classifications'][0])
        for key in lcsubs.keys():
            output[key] = lcsubs[key]
    except KeyError:
        pass

    try:
        output['year'] = extract_year(output['publish_date'])
    except KeyError:
        pass

    try:
        output['author'] = output['name']
    except KeyError:
        pass

    try:
        output['author_birth'] = extract_year(output['birth_date'])
        output['author_age']   = int(output['year']) - int(output['author_birth'])
    except:
        pass


    entries.append(output)
    #Periodically write out the results
    if len(entries)>1000:
        for individual in entries:
            catalog.write(json.dumps(individual) + "\n")
        print str(i*1000) + "\r"
        i = i+1
        entries = []

                 
for individual in entries:
    catalog.write(json.dumps(individual) + "\n")
