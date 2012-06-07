#!/usr/bin/python
import re

file = open("../../metadata/main.txt",'r')

fields = ["id","filename","htmlresult","year","month","day",]

i = 1
for line in file:
    metaData = line.split("\t")
    entry = dict()
    entry['year'] = str(metaData[2])
    entry['id'] = str(i)
    entry['filename'] = metaData[0]
    entry['htmlresult'] = "<a href=www.jstor.org/" + re.sub("_","/",metaData[0]) + ">" + metaData[6] + "</a>"
    returnData = []
    for field in fields:
        returnData.append(entry[field])
    print "\t".join(returnData)
    i = i+1
    if i>20:
        break

    
