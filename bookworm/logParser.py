import urllib
import os
import re
import gzip
import json
import sys

files = os.listdir("/var/log/apache2")

words = [] 

for file in files:
    reading = None
    if re.search("^access.log..*.gz",file):
        reading = gzip.open("/var/log/apache2/" + file)
    elif re.search("^access.log.*",file):
        reading = open("/var/log/apache2/" + file)
    else:
        continue
    sys.stderr.write(file + "\n")

    for line in reading:
        matches = re.findall(r"([0-9\.]+).*\[(.*)].*cgi-bin/dbbindings.py/?.query=([^ ]+)",line)
        for fullmatch in matches:
            t = dict()
            t['ip'] = fullmatch[0]
            match = fullmatch[2]
            try:
                data = json.loads(urllib.unquote(match).decode('utf8'))
            except ValueError:
                continue
            try:
                if isinstance(data['search_limits'],dict):
                    data['search_limits'] = [data['search_limits']]
                for setting in ['words_collation','database']:
                    try:
                        t[setting] = data[setting]
                    except KeyError:
                        t[setting] = ""
                for limit in data['search_limits']:
                    p = dict()
                    for constraint in ["word","TV_show","director"]:
                        try:
                            p[constraint] = p[constraint] + "," + (",".join(limit[constraint]))
                        except KeyError:
                            try:
                                p[constraint] = (",".join(limit[constraint]))
                            except KeyError:
                                p[constraint] = ""
                    for key in p.keys():
                        t[key] = p[key]
                    vals = [t[key] for key in ('ip','database','words_collation','word','TV_show','director')]
                    print "\t".join(vals).encode("utf-8")

                    
            except KeyError:
                raise

print len(words)
