import json

def convertToJSON(filename, location):
    """
    given a filename of a tsv, converts that into an ndjson
    file for Bookworm.
    """
    input = open(filename)
    output = open(location, "w")
    headers = input.readline()
    headers = headers.rstrip("\n")
    headers = headers.rstrip("\r")
    headers = headers.rstrip("\n")
    headers = headers.rstrip("\r")    
    headers = headers.split("\t")
    for line in input:
        line = line.rstrip("\n")
        line = line.rstrip("\r")
        line = line.rstrip("\n")
        line = line.rstrip("\r")        
        values = line.split("\t")
        myobject = dict(list(zip(headers,values)))
        output.write(json.dumps(myobject) + "\n")
    output.close()




