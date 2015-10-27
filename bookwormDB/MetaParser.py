from datetime import date
import datetime
import dateutil.parser
import json
import sys
import logging

fields_to_derive = []
fields = []
defaultDate = datetime.datetime(datetime.MINYEAR, 1, 1)

def DaysSinceZero(dateobj):
    #Zero isn't a date, which python knows but MySQL and javascript don't.
    return (dateobj - date(1,1,1)).days + 366

def ParseFieldDescs():
    global fields_to_derive
    global fields
    f = open('.bookworm/metadata/field_descriptions.json', 'r')
    try:
        fields = json.loads(f.read())
    except ValueError:
        raise ValueError("Error parsing JSON: Check to make sure that your field_descriptions.json file is valid?")
    f.close()

    derivedFile = open('.bookworm/metadata/field_descriptions_derived.json', 'w')
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
                tmp = dict(datatype="time", type="integer", unique=True)
                tmp["field"] = '_'.join([field["field"], derive["resolution"],
                                         derive["aggregate"]])
                output.append(tmp)
            else:
                tmp = dict(datatype="time", type="integer", unique=True)
                tmp["field"] = '_'.join([field["field"], derive["resolution"]])
                output.append(tmp)
    derivedFile.write(json.dumps(output))
    derivedFile.close()



def ParseJSONCatalog(target="default",source = "default"):
    global fields_to_derive
    if target=="default":
        target=open(".bookworm/metadata/jsoncatalog_derived.txt", "w")
    if source=="default":
        source = open(".bookworm/metadata/jsoncatalog.txt", "r")
        
    f = target
    for data in source:
        for char in ['\t', '\n']:
            data = data.replace(char, '')
        try:
            line = json.loads(data)
        except:
            sys.stderr.write('JSON Parsing Failed:\n%s\n' % data)
            continue
        for field in fields:
            # Smash together misidentified lists
            try:
                if field['unique'] and isinstance(line[field["field"]],list):
                    line[field["field"]] = "--".join(line[field["field"]])
            except KeyError:
                pass
        for field in fields_to_derive:
            """
            Using fields_to_derive as a shorthand for dates--this may break if we get more ambitious about derived fields,
            but this whole metadata-parsing code needs to be refactored anyway.

            Note: this code is inefficient--it parses the same date multiple times. We should be parsing the date once and pulling 
            derived fields out of that one parsing.
            """
            try:
                if line[field["field"]]=="":
                    # Use blankness as a proxy for unknown
                    continue

                time = dateutil.parser.parse(line[field["field"]],default = defaultDate)
                intent = [time.year,time.month,time.day]
                content = [str(item) for item in intent]
                
                pass
            except:
                """
                Fall back to parsing as strings
                """
                try:
                    datem = line[field["field"]].split("T")[0]
                    content = datem.split('-')
                    intent = [int(item) for item in content]
                except KeyError:
                    #It's OK not to have an entry for a time field
                    continue
                except ValueError:
                    # Thrown if fields are empty on taking the int value: treat as junk
                    continue
                except AttributeError:
                    """
                    Happens if it's an integer, which is a forgiveable way
                    to enter a year:
                    """
                    content = [str(line[field['field']])]
                    intent = [line[field['field']]]
            if not content:
                continue
            else:
                for derive in field["derived"]:
                    try:
                        if "aggregate" in derive:
                            if derive["resolution"] == 'day' and \
                                    derive["aggregate"] == "year":
                                k = "%s_day_year" % field["field"]
                                dt = date(intent[0], intent[1], intent[2])
                                line[k] = dt.timetuple().tm_yday
                            elif derive["resolution"] == 'day' and \
                                    derive["aggregate"] == "month":
                                k = "%s_day_month" % field["field"]
                                line[k] = intent[2]
                            elif derive["resolution"] == 'day' and \
                                    derive["aggregate"] == "week":
                                k = "%s_day_month" % field["field"]
                                dt = date(intent[0], intent[1], intent[2])
                                #Python and javascript handle weekdays differently:
                                #Like JS, we want to begin on Sunday with zero
                                line[k] = dt.weekday() + 1
                                if (line[k])==7: line[k] = 0
                            elif derive["resolution"] == 'month' and \
                                    derive["aggregate"] == "year":
                                k = "%s_month_year" % field["field"]
                                dt = date(1,intent[1],1)
                                line[k] = dt.timetuple().tm_yday
                            elif derive["resolution"] == 'week' and \
                                    derive["aggregate"] == "year":
                                dt = date(intent[0], intent[1], intent[2])
                                k = "%s_week_year" % field["field"]
                                line[k] = int(dt.timetuple().tm_yday/7)*7
                            elif derive["resolution"] == 'hour' and \
                                    derive["aggregate"] == "day":
                                k = "%s_hour_day" % field["field"]
                                line[k] = time.hour
                            elif derive["resolution"] == 'minute' and \
                                    derive["aggregate"] == "day":
                                k = "%s_hour_day" % field["field"]
                                line[k] = time.hour*60 + time.minute
                            else:
                                logging.warning('Problem with aggregate resolution.')
                                continue
                        else:
                            if derive["resolution"] == 'year':
                                line["%s_year" % field["field"]] = intent[0]
                            elif derive["resolution"] == 'month':
                                try:
                                    k = "%s_month" % field["field"]
                                    dt = date(intent[0], intent[1], 1)
                                    line[k] = DaysSinceZero(dt)
                                except:
                                    logging.warning("Problem with date fields\n")
                                    pass
                            elif derive['resolution'] == 'week':
                                k = "%s_week" % field['field']
                                dt = date(intent[0], intent[1], intent[2])
                                inttime = DaysSinceZero(dt)
                                time = int(inttime/7)*7
                                #Not starting on Sunday or anything funky like that. Actually, I don't know what we're starting on. Adding an integer here would fix that.
                                line[k] = time
                            elif derive['resolution'] == 'day':
                                k = "%s_day" % field['field']
                                dt = date(intent[0], intent[1], intent[2])
                                inttime = DaysSinceZero(dt)
                                line[k] = inttime
                            else:
                                logging.warning('Resolution %s currently not supported.' %(derive['resolution']))
                                continue
                    except ValueError:
                        # One of out a million Times articles threw this with
                        # a year of like 111,203. It's not clear how best to
                        # handle this.
                        logging.warning( "ERROR: %s " % line[field["field"]] + \
                              "did not convert to proper date. Moving on...")
                        #raise
                        pass
                    except Exception, e:
                        logging.warning( '*'*50)
                        logging.warning('ERROR: %s\nINFO: %s\n' % (str(e), e.__doc__))
                        logging.warning( '*'*50)
                line.pop(field["field"])
        f.write('%s\n' % json.dumps(line))
        f.flush()
    f.close()

def parse_initial_catalog(target=sys.stdout,source=sys.stdin):
    ParseFieldDescs()
    ParseJSONCatalog(target=target,source=source)
    
if __name__=="__main__":
    ParseFieldDescs()
    ParseJSONCatalog(target=sys.stdout,source=sys.stdin)
