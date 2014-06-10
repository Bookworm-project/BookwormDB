from datetime import date, datetime
import json


fields_to_derive = []


def DaysSinceZero(dateobj):
    numdays = 0
    for yr in range(dateobj.year):
        if yr % 4 == 0 and (yr % 100 != 0 or yr % 100 == 0 and yr % 400 == 0):
            numdays += 366
        else:
            numdays += 365
    curr_date = date(dateobj.year, dateobj.month, dateobj.day)
    numdays += curr_date.timetuple().tm_yday
    return numdays


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


def ParseJSONCatalog():
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
                intent = [int(item) for item in content]
            except KeyError:
                #It's OK not to have an entry for a time field
                continue
            except ValueError:
                # Thrown if fields are empty on taking the int value: treat as junk
                continue
            except AttributeError:
                # Happens if it's an integer, which is a forgiveable way
                # to enter a year:
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
                                line[k] = str(dt.timetuple().tm_yday)
                            elif derive["resolution"] == 'month' and \
                                    derive["aggregate"] == "year":
                                k = "%s_month_year" % field["field"]
                                line[k] = content[1]
                            elif derive["resolution"] == 'day' and \
                                    derive["aggregate"] == "month":
                                k = "%s_day_month" % field["field"]
                                line[k] = content[2]
                            elif derive["resolution"] == 'week' and \
                                    derive["aggregate"] == "year":
                                dt = date(intent[0], intent[1], intent[2])
                                k = "%s_week_year" % field["field"]
                                line[k] = str(int(dt.timetuple().tm_yday/7))
                            else:
                                print 'Problem with aggregate resolution.'
                                continue
                        else:
                            if derive["resolution"] == 'year':
                                line["%s_year" % field["field"]] = content[0]
                            elif derive["resolution"] == 'month':
                                try:
                                    dt = datetime(intent[0], intent[1], 1)
                                    k = "%s_month" % field["field"]
                                    line[k] = DaysSinceZero(dt)
                                except:
                                    print 'Problem with date fields:', intent
                                    pass
                            elif derive['resolution'] == 'week':
                                k = "%s_week" % field['field']
                                dt1 = date(intent[0], intent[1], intent[2])
                                dt2 = date(1, 1, 1)
                                line[k] = str(int((dt1 - dt2).days/7)*7)
                            elif derive["resolution"] == 'day':
                                try:
                                    k = "%s_day" % field["field"]
                                    #dtstr = '%02d%02d%s' % (int(content[2]),
                                    #                        int(content[1]),
                                    #                        content[0])
                                    #dt = datetime.strptime(dtstr, "%d%m%Y")
                                    #dtdiff = dt.date() - date(1, 1, 1)
                                    dtdiff = date(content[0],content[1],content[2]) - date(1,1,1)
                                    line[k] = str(dtdiff.days)
                                except:
                                    pass
                            else:
                                print 'Resolution currently not supported.'
                                continue
                    except ValueError:
                        # One of out a million Times articles threw this with
                        # a year of like 111,203. It's not clear how best to
                        # handle this.
                        print "ERROR: %s " % line[field["field"]] + \
                              "did not convert to proper date. Moving on..."
                        pass
                    except Exception, e:
                        print '*'*50
                        print '   ---   Different error occured ---   '
                        print 'ERROR: %s\nINFO: %s' % (str(e), e.__doc__)
                        print '*'*50
                line.pop(field["field"])
        f.write('%s\n' % json.dumps(line))
        f.flush()
    f.close()
