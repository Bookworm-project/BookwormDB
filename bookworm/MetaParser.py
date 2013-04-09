import datetime
import json


fields_to_derive = []

def ParseFieldDescs():
    f = open('files/metadata/field_descriptions.json', 'r')
    fields = json.loads(f.read())
    f.close()
    
    derivedFile = open('files/metadata/field_descriptions_derived.json', 'w')
    output = []
    
    for field in fields:
        if field["datatype"] == "time":
             if "derived" in field:
                 fields_to_derive.append(field)
             else:
                 output.append(field)
        else:
            output.append(field)
    
    for field in fields_to_derive:
        for derive in field["derived"]:
            if "aggregate" in derive:
                tmpdct = {
                          "field": '_'.join([field["field"], derive["resolution"], derive["aggregate"]]),
                          "datatype": "time",
                          "type": "integer",
                          "unique": True
                         }
                output.append(tmpdct)
            else:
                tmpdct = {
                          "field": '_'.join([field["field"], derive["resolution"]]),
                          "datatype": "time",
                          "type": "integer",
                          "unique": True
                         }
                output.append(tmpdct)
    derivedFile.write(json.dumps(output))
    derivedFile.close()


def ParseJSONCatalog():
    order = ["year", "month", "week", "day"]
    f = open("files/metadata/jsoncatalog_derived.txt", "w")
    
    for data in open("files/metadata/jsoncatalog.txt", "r"):
        for char in ['\t', '\n']:
            data = data.replace(char, '')
        try:
            line = json.loads(data)
        except:
            print 'JSON Parsing Failed:\n%s\n' % data
            pass
        
        for field in fields_to_derive:
            try:
                content = line[field["field"]].split('-')
                intent  = [int(item) for item in content]
            except KeyError:
                continue
            except ValueError:
                #thrown if fields are empty on taking the int
                continue
            except AttributeError:
                #Happens if it's an integer,which is a forgiveable way to enter a year:
                content = [str(line[field['field']])]
                intent = [line[field['field']]]
    
            if len(content) == 0:
                continue
            else:
                to_derive = field["derived"]
                for derive in to_derive:
                    try:
                        if "aggregate" in derive:
                            if derive["resolution"] == 'day' and derive["aggregate"] == "year":
                                line[field["field"] + "_day_year"] = str(datetime.datetime(intent[0],intent[1],intent[2]).timetuple().tm_yday)
                            if derive["resolution"] == 'month' and derive["aggregate"] == "year":
                                line[field["field"] + "_month_year"] = content[1]
                            elif derive["resolution"] == 'day' and derive["aggregate"] == "month":
                                line[field["field"] + "_day_month"] = content[2]
                            elif derive["resolution"] == 'week' and derive["aggregate"] == "year":
                                yearday = datetime.datetime(intent[0],intent[1],intent[2]).timetuple().tm_yday
                                line[field["field"] + "_week_year"] = str(int(yearday/7))
                            else:
                                continue
                        else:
                            if derive["resolution"] == 'year':
                                line[field["field"] + "_year"] = content[0]
                            elif derive["resolution"] == 'month':
                                line[field["field"] + "_month"] = str(int((datetime.date(intent[0],intent[1],1) - datetime.date(1,1,1)).days))
                            elif derive['resolution'] == 'week':
                                line[field['field'] + "_week"] = str(int((datetime.date(intent[0],intent[1],intent[2]) - datetime.date(1,1,1)).days/7)*7)
                            elif derive["resolution"] == 'day':
                                line[field["field"] + "_day"] = str((datetime.datetime.strptime('%02d'%int(content[2])+'%02d'%int(content[1])+content[0], "%d%m%Y").date() - datetime.date(1,1,1)).days)
                            else:
                                continue
                    except ValueError:
                        #one of out a million Times articles threw this with a year of like 111,203.
                        #It's not clear how best to handle this.
                        print "Something's wrong with " + line[field["field"]] + " as a date--moving on..."
                        pass
                line.pop(field["field"])
        f.write('%s\n' % json.dumps(line))
    f.close()