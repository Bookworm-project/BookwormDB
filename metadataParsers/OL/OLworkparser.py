import json,sys

sys.path.append("..")
sys.path.append("../includes/nameparser-0.2.3")

from parsingClasses import *
from nameparser import HumanName


works = "../../../Downloads/Catinfo/ol_dump_works_latest.txt"

work_vars = ["subject_places","subject_people","subjects"]

outputs = dict()
for var in work_vars:
    outputs[var] = open("../../../metadata/" + var + ".txt",'w')

print "Loading Work Data..." 

for line in open(works):
    try:
        outsidedata = dict()
        entry = json.loads(line.split("\t")[4])
        key = entry['key']
        for variable in work_vars: 
            try:
                for item in entry[variable]:
                    if variable == 'subject_people':
                        item = to_unicode(item)
                        try:
                            name = HumanName(item)
                            first = name.first
                            last = name.last
                        except KeyError or ValueError:
                            first = ''
                            last = ''
                        output = "\t".join([key,item,first,last])+"\n"
                        outputs[variable].write(output.encode('utf-8'))
                    else:
                        item = item.encode('UTF-8')
                        output = key + "\t" + item.decode('UTF-8') + "\n"
                        #print output
                        outputs[variable].write(output.encode('utf-8'))
            except:
                #There can be ValueErrors (where the key doesn't exist) or TypeErrors (b/c OL uses a hash every once in
                #a while for reasons I don't get.
                pass
               
    except:
        raise

print "Work Data Loaded" 
