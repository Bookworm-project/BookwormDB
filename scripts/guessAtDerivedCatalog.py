#!/usr/bin/python

import json
import re
input = open("files/metadata/jsoncatalog.txt")

"""
This doesn't work amazing, but with some polishing and integration with Dublin core standards it might.

"""
i = 1

allMyKeys = dict()

for line in input:
    i += 1
    entry = json.loads(line)
    for key in entry:
        try: 
            allMyKeys[key][entry[key]] += 1
        except KeyError:
            try:
                allMyKeys[key][entry[key]] = 1
            except KeyError:
                allMyKeys[key] = dict()
                allMyKeys[key][entry[key]] = 1
    if i > 30000:
        break


def guessBasedOnNameAndContents(metadataname,dictionary):

    description = {"field":metadataname,"datatype":"etc","type":"text","unique":True}

    example = dictionary.keys()[0]
    
    if type(example)==int:
        description["type"] = "integer"
    if type(example)==list:
        unique(example)==False

    if metadata == "searchstring":
        return {"datatype": "searchstring", "field": "searchstring", "unique": True, "type": "text"}

    if re.search("date",metadataname) or re.search("time",metadataname):
        description["datatype"] = "time"

    values = [dictionary[key] for key in dictionary]
    averageNumberOfEntries = sum(values)/len(values)
    maxEntries = max(values)

    print metadataname
    print averageNumberOfEntries
    print maxEntries
    if averageNumberOfEntries > 2:
        description["datatype"] = "categorical"

    return description
    
myOutput = []
for metadata in allMyKeys:
    bestGuess = guessBasedOnNameAndContents(metadata,allMyKeys[metadata])
    myOutput.append(bestGuess)

myOutput = [output for output in myOutput if output["field"] != "filename"]

output = open("files/metadata/field_descriptions.json","w")

output.write(json.dumps(myOutput))
