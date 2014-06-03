import json
import sys
import re

def convertToJSON(filename):
    """
    given a filename of a tsv, converts that into a one-per-line set of json
    documents that can be more easily read into the Bookworm.
    """
    input = open(filename)
    output = open("tmp.txt","w")
    headers = input.readline()
    headers = headers.rstrip("\n")
    headers = headers.split("\t")
    for line in input:
        line = line.rstrip("\n")
        values = line.split("\t")
        myobject = dict(zip(headers,values))
        output.write(json.dumps(myobject) + "\n")

    output.close()


        
        
