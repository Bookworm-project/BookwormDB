import json
import datetime
import time
import sys
import os


PROJECT = sys.argv[1]

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

f = open("../metadata/field_descriptions.json", "r")
fields = json.loads(f.read())
f.close()

fields_to_derive = []

ensure_dir("metadataParsers/" + PROJECT + '/' + PROJECT + ".json")
f = open("metadataParsers/" + PROJECT + '/' + PROJECT + ".json", "w")

output = []

for field in fields:
    if field["datatype"] == "time":
         if "derived" in field: fields_to_derive.append(field)
         else: output.append(field)
    else: output.append(field)

for field in fields_to_derive:
    for derive in field["derived"]:
        if "aggregate" in derive: output.append({"field":'_'.join([field["field"], derive["resolution"], derive["aggregate"]]), "datatype":"time", "type":"integer", "unique":True})
        else: output.append({"field":'_'.join([field["field"], derive["resolution"]]), "datatype":"time", "type":"integer", "unique":True})

f.write(json.dumps(output))
f.close()

f = open("../metadata/jsoncatalog.txt", "r")
md = f.readlines()
f.close()

order = ["year", "month", "week", "day"]

f = open("../metadata/jsoncatalog_derived.txt", "w")
for data in md:
    line = json.loads(data)
    for field in fields_to_derive:
        try:
            content = line[field["field"]].split('-')
        except KeyError:
            continue
        except AttributeError:
            #Happens if it's an integer,which is a forgiveable way to enter a year:
            content = [str(line[field['field']])]
            
        if len(content) == 0: continue
        else:
            to_derive = field["derived"]
            for derive in to_derive:
                if "aggregate" in derive:
                    if derive["resolution"] == 'day' and derive["aggregate"] == "year": line[field["field"] + "_day_year"] = content[2]
                    elif derive["resolution"] == 'month' and derive["aggregate"] == "year": line[field["field"] + "_month_year"] = content[1]
                    else: continue
                else:
                    if derive["resolution"] == 'year': line[field["field"] + "_year"] = content[0]
                    elif derive["resolution"] == 'month': line[field["field"] + "_month"] = (datetime.datetime.strptime('%02d'%int(content[1])+content[0], "%m%Y").date() - datetime.date(1,1,1)).days
                    elif derive["resolution"] == 'day': line[field["field"] + "_day"] = (datetime.datetime.strptime('%02d'%int(content[2])+'%02d'%int(content[1])+content[0], "%d%m%Y").date() - datetime.date(1,1,1)).days
                    else: continue
            line.pop(field["field"])
    f.write(json.dumps(line) + '\n')

f.close()
    
