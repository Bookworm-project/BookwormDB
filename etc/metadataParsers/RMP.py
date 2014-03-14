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


    d = output["date"].split("/")
    century = "20"
    if d[0]=="99":
        century = "19"
    try:
        output["date"] = "-".join(["20" + d[2],d[0],d[1]])
    except:
        pass

    output["filename"] = output["ratingName"]
    output["searchstring"] = " ".join(["name","school","comment"])
    print json.dumps(output)
