import json
import datetime
import time
import sys

PROJECT = sys.argv[1]

f = open("../metadata/jsoncatalog.txt", "r")
md = f.readlines()
f.close()

f = open("../metadata/field_descriptions.json", "r")
fields = json.loads(f.read())
f.close()

fields_to_derive = []

output = []

f = open("metadataParsers/" + PROJECT + '/' + PROJECT + ".json", "w")
f.write('[')

for field in fields:
    if field["datatype"] == "time":
         if "derived" in field: fields_to_derive.append(field)
         else: f.write(json.dumps(field) + ', ')
    else: f.write(json.dumps(field) + ', ')

output = []
for field in fields_to_derive:
    for derive in field["derived"]:
        output.append({"field":str(json.dumps(field["field"])[1:-1] + '_' + json.dumps(derive)[1:-1]), "datatype":"time", "type":"integer", "unique":True})
f.write(str(output)[1:])
f.close()


f = open("../metadata/jsoncatalog_derived.txt", "w")
for data in md:
    line = json.loads(data)
    for field in fields_to_derive:
        content = line[field["field"]].split('-')
        if len(content) in [0,1]: continue
        else:
            to_derive = field["derived"]
            for derive in to_derive:
                l = derive.split("_")
                if len(l) == 1:
                    if l[0] == "year": line[field["field"] + "_year"] = content[0]
                    else: continue
                else:
                    if l[0] == "month":
                        if l[1] == "round": line[field["field"] + "_month_round"] = (datetime.datetime.strptime('%02d'%int(content[1])+content[0], "%m%Y").date() - datetime.date(1,1,1)).days
                        elif l[1] == "cycle": line[field["field"] + "_month_cycle"] = content[1]
                    elif l[0] == "day":
                        if l[1] == "round": line[field["field"] + "_day_round"] = (datetime.datetime.strptime('%02d'%int(content[2])+'%02d'%int(content[1])+content[0], "%d%m%Y").date() - datetime.date(1,1,1)).days
                        elif l[1] == "cycle": line[field["field"] + "_day_cycle"] = content[2]
            line.pop(field["field"])
    f.write(json.dumps(line) + '\n')
f.close()
    
