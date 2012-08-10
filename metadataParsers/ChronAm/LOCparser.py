#!/usr/bin/python

#Just running this to get the names:
#find LOCpapers/NewspaperFiles/ -name "*.txt" -exec basename {} \; > papers.txt

import re
import os
import json
import subprocess

filelist = open("../../../texts/papers.txt")
metadata = open('../../../metadata/jsoncatalog.txt','w')
for line in filelist:
    try:
        mydict = dict()
        raw = line
        line = re.sub(".txt\n","",line)
        line = line.split("_")
        mydict['paperid'] = line[0]
        mydict['page'] = int(line[2])
        dates = line[1].split("-")
        mydict['year'] = int(dates[0])
        mydict['month'] = int(dates[1])
        mydict['day'] = int(dates[2])
        mydict['date'] = '-'.join([str(dates[0]),str(dates[1]),str(dates[2])])
        mydict['filename'] = re.sub(".txt\n","",raw)
        LOCbase = "http://chroniclingamerica.loc.gov/lccn/" + line[0] + "/" + "-".join([dates[0],dates[1],dates[2]]) + "/ed-1/seq-" + line[2] + "/"
        mydict['searchstring'] = "<img src=" + LOCbase + "thumbnail.jpg></img>  <a href = " + LOCbase+ "> Read page at LOC.gov</a>"
        metadata.write(json.dumps(mydict)+"\n")
    except:
        #some lines are throwing errors. Just skipping them until it's proved bad to do so.
        pass

metadata.close()
