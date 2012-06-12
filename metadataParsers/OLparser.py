#!/usr/bin/python

import json
import re
import copy
import codecs

input    = open("../../Downloads/Catinfo/ocaidbooks.txt")
#Our unique identifier

#OL stores variable in structures that have to be treated differently
singleVars = ["ocaid","title","publish_country","publish_date","key"]
multiVars  = ["lc_classifications","oclc_numbers","lccn","publish_places","publishers"]
hashVars   = ["languages","works","authors"]

catalog = open("../../Downloads/Catinfo/cleaned/catalog.txt",'w')
othercats = dict()
for multiVar in multiVars+hashVars:
    othercats[multiVar] = open("../../Downloads/Catinfo/cleaned/" + multiVar + ".txt",'w')

bookid  = 1

entries  = []

for line in input:
    entry = json.loads(line.split("\t")[4])
    etype = re.sub(".*/","",entry['type']['key'])
    localhash = {"multi":{},"single":{}}
    if etype=="edition":
        #Don't keep all the html junk about the type of key
        entry['key'] = re.sub(".*/","",entry['key'])
        localhash['bookid'] = copy.deepcopy(bookid)
        bookid = bookid+1
        for singleVar in singleVars:
            localhash["single"][singleVar] = entry.setdefault(singleVar,"").encode("utf-8")
        for multiVar in multiVars:
            localhash["multi"][multiVar] = entry.setdefault(multiVar,[])
        for hashVar in hashVars:
            tmpresults = []
            for lochash in entry.setdefault(hashVar,[]):
                tmpresults.append(re.sub(".*/","",lochash['key']))
            localhash["multi"][hashVar] = tmpresults
    if etype=="author":
        pass
    if etype=="work":
        pass
    entries.append(localhash)
    #Periodically write out the results
    if len(entries)>1000:
        for entry in entries:
            if entry["single"]["ocaid"] != "":
                catline = [str(entry['bookid'])]
                for singleVar in singleVars:
                    catline.append(entry["single"][singleVar])
                catline = "\t".join(catline) + "\n"
                catalog.write(catline)
                for multiVar in multiVars + hashVars:
                    for datum in entry["multi"][multiVar]:
                        lineout = str(entry["bookid"]) + "\t" + str(datum.encode('utf-8')) + "\n"
                        othercats[multiVar].write(lineout)
        entries = []
