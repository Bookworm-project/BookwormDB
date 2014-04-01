import rdflib
import json


g=rdflib.Graph()
g.load("newspapers.rdf")


seen = dict()

for s,p,o in g:
    try:
        seen[s][p] = o
    except:
        seen[s] = dict()
        seen[s][p]] = o

def convertID(string):
    try:
        re.findall("lccn/(.*)#title",string)[0]
    except IndexError:
        return False


jsoncatalog = []

for name in seen.keys():
    id = convertID(name)
    if id:
        attributes = dict()
        attributes['paperid'] = id
        for attribute in seen[name].keys():
            attributes[attribute] = seen[name][attribute]
        jsoncatalog.append(attribute)

for line in jsoncatalog:
    print json.dumps(line)

