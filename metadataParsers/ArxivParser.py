#!/usr/bin/py

import re

month = "1001"
file = "0531"

def parse_file(month,file,get_metadata_names=False):
    INFILE = open("../metadata/" + month + "/" + month + "." + file + ".abs",'r')
    mode = "start"
    data = {'abstract':[""]}
    for line in INFILE:
        if mode=="metadata":
            matches = re.match("(?P<field>\w+)\: ?(?P<value>.*$)",line)
            if matches:
                data[matches.group("field")] = matches.group("value")
        if mode=="abstract":
            data['abstract'].append(line)
        if re.match(r"\\",line):
            if mode=="abstract":
                break
            if mode=="metadata":
                mode = "abstract"
            if mode=="start":
                mode="metadata"
    if get_metadata_names:
        return data.keys()
    if not get_metadata_names:
        value = []
        for key in ["ArXiv:",'From',"License",'Title','abstract','Comments','Authors',"date","Categories"]:
            value.append(data.get(key,""))
        return value
        
        
counts = dict()

for i in range(1000,5000):
    keys = parse_file("1001",str(i),get_metadata_names=True)
    for key in keys:
        z = counts.get(key, 0)
        counts[key] = z+1

print counts
