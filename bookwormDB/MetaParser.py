from __future__ import division
from datetime import date
import datetime
import dateutil.parser
import json
import sys
import os
import logging
from multiprocessing import Queue, Process
from queue import Empty
from .multiprocessingHelp import mp_stats, running_processes
import time


defaultDate = datetime.datetime(datetime.MINYEAR, 1, 1)

def DaysSinceZero(dateobj):
    #Zero isn't a date, which python knows but MySQL and javascript don't.
    return (dateobj - date(1,1,1)).days + 366


mySQLreservedWords = set(["ACCESSIBLE", "ADD",
"ALL", "ALTER", "ANALYZE", "AND", "AS", "ASC", "ASENSITIVE", "BEFORE",
"BETWEEN", "BIGINT", "BINARY", "BLOB", "BOTH", "BY", "CALL",
"CASCADE", "CASE", "CHANGE", "CHAR", "CHARACTER", "CHECK", "COLLATE",
"COLUMN", "CONDITION", "CONSTRAINT", "CONTINUE", "CONVERT", "CREATE",
"CROSS", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
"CURRENT_USER", "CURSOR", "DATABASE", "DATABASES", "DAY_HOUR",
"DAY_MICROSECOND", "DAY_MINUTE", "DAY_SECOND", "DEC", "DECIMAL",
"DECLARE", "DEFAULT", "DELAYED", "DELETE", "DESC", "DESCRIBE",
"DETERMINISTIC", "DISTINCT", "DISTINCTROW", "DIV", "DOUBLE", "DROP",
"DUAL", "EACH", "ELSE", "ELSEIF", "ENCLOSED", "ESCAPED", "EXISTS",
"EXIT", "EXPLAIN", "FALSE", "FETCH", "FLOAT", "FLOAT4", "FLOAT8",
"FOR", "FORCE", "FOREIGN", "FROM", "FULLTEXT", "GENERAL", "GRANT",
"GROUP", "HAVING", "HIGH_PRIORITY", "HOUR_MICROSECOND", "HOUR_MINUTE",
"HOUR_SECOND", "IF", "IGNORE", "IGNORE_SERVER_IDS", "IN", "INDEX",
"INFILE", "INNER", "INOUT", "INSENSITIVE", "INSERT", "INT", "INT1",
"INT2", "INT3", "INT4", "INT8", "INTEGER", "INTERVAL", "INTO", "IS",
"ITERATE", "JOIN", "KEY", "KEYS", "KILL", "LEADING", "LEAVE", "LEFT",
"LIKE", "LIMIT", "LINEAR", "LINES", "LOAD", "LOCALTIME",
"LOCALTIMESTAMP", "LOCK", "LONG", "LONGBLOB", "LONGTEXT", "LOOP",
"LOW_PRIORITY", "MASTER_HEARTBEAT_PERIOD[c]",
"MASTER_SSL_VERIFY_SERVER_CERT", "MATCH", "MAXVALUE", "MEDIUMBLOB",
"MEDIUMINT", "MEDIUMTEXT", "MIDDLEINT", "MINUTE_MICROSECOND",
"MINUTE_SECOND", "MOD", "MODIFIES", "NATURAL", "NOT",
"NO_WRITE_TO_BINLOG", "NULL", "NUMERIC", "ON", "OPTIMIZE", "OPTION",
"OPTIONALLY", "OR", "ORDER", "OUT", "OUTER", "OUTFILE", "PRECISION",
"PRIMARY", "PROCEDURE", "PURGE", "RANGE", "READ", "READS",
"READ_WRITE", "REAL", "REFERENCES", "REGEXP", "RELEASE", "RENAME",
"REPEAT", "REPLACE", "REQUIRE", "RESIGNAL", "RESTRICT", "RETURN",
"REVOKE", "RIGHT", "RLIKE", "SCHEMA", "SCHEMAS", "SECOND_MICROSECOND",
"SELECT", "SENSITIVE", "SEPARATOR", "SET", "SHOW", "SIGNAL",
"SLOW[d]", "SMALLINT", "SPATIAL", "SPECIFIC", "SQL", "SQLEXCEPTION",
"SQLSTATE", "SQLWARNING", "SQL_BIG_RESULT", "SQL_CALC_FOUND_ROWS",
"SQL_SMALL_RESULT", "SSL", "STARTING", "STRAIGHT_JOIN", "TABLE",
"TERMINATED", "THEN", "TINYBLOB", "TINYINT", "TINYTEXT", "TO",
"TRAILING", "TRIGGER", "TRUE", "UNDO", "UNION", "UNIQUE", "UNLOCK",
"UNSIGNED", "UPDATE", "USAGE", "USE", "USING", "UTC_DATE", "UTC_TIME",
"UTC_TIMESTAMP", "VALUES", "VARBINARY", "VARCHAR", "VARCHARACTER",
"VARYING", "WHEN", "WHERE", "WHILE", "WITH", "WRITE", "XOR",
"YEAR_MONTH", "ZEROFILL", "WORDS", "NWORDS", "WORD", "UNIGRAM"])


def ParseFieldDescs(write = False):
    f = open('field_descriptions.json', 'r')
    try:
        fields = json.loads(f.read())
    except ValueError:
        raise ValueError("Error parsing JSON: Check to make sure that your field_descriptions.json file is valid.")

    if write:
        derivedFile = open('.bookworm/metadata/field_descriptions_derived.json', 'w')

    output = []

    fields_to_derive = []

    for field in fields:
        if field["field"].upper() in mySQLreservedWords:
            raise NameError(f"{field['field']} is a reserved word but appears"
            "in field_description.json. Please choose a different name for"
            "the column.")
        for character in [" ","-", "&","+","."]:
            if character in field['field']:
                raise NameError(f"{field['field']} contains a special character, please rename")

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
    if write:
        derivedFile.write(json.dumps(output))
        derivedFile.close()

    return (fields_to_derive, fields)


def parse_json_catalog(line_queue, processes, modulo):
    fields_to_derive, fields = ParseFieldDescs(write = False)

    if os.path.exists("jsoncatalog.txt"):
        mode = "json"
        fin = open("jsoncatalog.txt")

    if os.path.exists("catalog.csv"):
        mode = "csv"
        import csv
        fin = csv.DictReader("catalog.csv")

    for i, line in enumerate(fin):
        if i % processes != modulo:
            continue

        for char in ['\t', '\n']:
            line = line.replace(char, '')

        if mode == "json":
            try:
                line = json.loads(line)
            except:
                logging.error(f"Invalid json in line {i}\n:{line}"
                "The input file must be in ndjson format (http://ndjson.org/)")
                raise

        for field in fields:
            # Smash together misidentified lists
            try:
                if field['unique'] and isinstance(line[field["field"]],list):
                    line[field["field"]] = "--".join(line[field["field"]])
            except KeyError:
                pass

        for field in fields_to_derive:

            """
            Using fields_to_derive as a shorthand for dates--this may break
            if we get more ambitious about derived fields,
            but this whole metadata-parsing code needs to be refactored anyway.

            Note: this code is inefficient--it parses the same date multiple times.
            We should be parsing the date once and pulling
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
                                # Python and javascript handle weekdays differently:
                                # Like JS, we want to begin on Sunday with zero
                                line[k] = dt.weekday() + 1
                                if (line[k]) == 7:
                                    line[k] = 0
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
                                logging.warning('Resolution %s currently not supported.' % (derive['resolution']))
                                continue
                    except ValueError:
                        # One of out a million Times articles threw this with
                        # a year of like 111,203. It's not clear how best to
                        # handle this.
                        logging.warning("ERROR: %s " % line[field["field"]] +
                                        "did not convert to proper date. Moving on...")
                        # raise
                        pass
                    except Exception as e:
                        logging.warning('*'*50)
                        logging.warning('ERROR: %s\nINFO: %s\n' % (str(e), e.__doc__))
                        logging.warning('*'*50)
                line.pop(field["field"])
        try:
            el = json.dumps(line)
            line_queue.put((line["filename"], el))
        except KeyError:
            logging.warning("No filename key in {}".format(line))
        except:
            logging.warning("Error on {}".format(line))
            raise
    logging.debug("Metadata thread done after {} lines".format(i))


def parse_catalog_multicore():
    from .sqliteKV import KV
    cpus, _ = mp_stats()
    encoded_queue = Queue(10000)
    workers = []

    for i in range(cpus):
        p = Process(target = parse_json_catalog, args = (encoded_queue, cpus, i))
        p.start()
        workers.append(p)
    output = open(".bookworm/metadata/jsoncatalog_derived.txt", "w")

    bookids = KV(".bookworm/metadata/textids.sqlite")
    import sqlite3

    while True:
        try:
            filename, n = encoded_queue.get_nowait()
            output.write(n + "\n")
            ids = set()
            try:
                bookids.register(filename)
            except sqlite3.IntegrityError:
                if filename in ids:
                    logging.warning("Duplicate key insertion {}".format(filename))
            ids.add(filename)

        except Empty:
            if running_processes(workers):
                # Give it a sec to fill back up to avoid this thread taking up
                # a full processor.
                time.sleep(0.01)
            else:
                # We're done!
                break

    bookids.close()
    output.close()
