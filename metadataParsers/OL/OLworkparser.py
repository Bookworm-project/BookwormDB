import json,sys

sys.path.append("..")

from parsingClasses import *
from nameparser import HumanName


works = "../../../Downloads/Catinfo/ol_dump_works_latest.txt"

work_vars = ["subject_places","subject_people","subjects"]

outputs = dict()
#for var in work_vars:
#    outputs[var] = open("../../../metadata/" + var + ".txt",'w')
output = open("../../../metadata/jsonworks.txt",'w')

print "Loading Work Data..." 

for line in open(works):
    try:
        outputline = dict()
        entry = json.loads(line.split("\t")[4])
        key = entry['key']
        outputline['works'] = key
        for variable in work_vars:
            try: outputline['subjectPlace'] = entry['subject_places']
            except KeyError:pass
            try: outputline['subject'] = entry['subjects']
            except KeyError:pass
            try:
                outputline['subjectPerson'] = entry['subject_people']
                try:
                    outputline['subjectFirstName'] = []
                    outputline['subjectLastName'] = []
                    for item in entry['subject_people']:
                        name = HumanName(item)
                        first = name.first
                        last = name.last
                        outputline['subjectFirstName'].append(first)
                        outputline['subjectLastName'].append(last)
                except:
                    pass
            except KeyError:
                pass
        if len(outputline.keys()) > 1:
            output.write(json.dumps(outputline) + "\n")

    except:
        raise
