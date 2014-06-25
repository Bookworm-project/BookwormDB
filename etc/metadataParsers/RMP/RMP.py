import sys
import json
import re

for line in sys.stdin:
    line = line.strip()
    output = dict()
    line = re.sub("&nbsp;"," ",line)
    input = line.split("\t")
    for variable in ["ID", "ratingName", "date", "class", "rEasy", "rHelpful", "rClarity", "rInterest", "rGrade", "comment", "name", "school", "location", "department", "ratings", "quality", "helpfulness", "clarity", "easiness"]:
        output[variable] = input.pop(0)

    output["searchstring"] = output["name"] + " (" + output["school"] + ") " + output["comment"]
    del output["comment"]

    d = output["date"].split("/")
    try:
        killDate = False
        year = int("20" + d[2])
        if year > 2015:
            year = year-100
        if year > 2015:
            killDate = True
        if year <  1990:
            killDate = True
        output["date"] = "-".join([str(year),d[0],d[1]])
        
    except:
        killDate = True
    
    if killDate:
        del output["date"]
    
    output["filename"] = output["ratingName"]

    print json.dumps(output)
