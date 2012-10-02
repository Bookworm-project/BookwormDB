#!/usr/bin/python

import os
import re
filenames = [filename for filename in os.listdir("../../../texts/raw") if not (re.search('zip',filename) or re.search('3gram',filename))]
for filename in filenames:
    towrite = dict()
    print filename
    reading = open("../../../texts/raw/" + filename)
    corpus = re.sub("-2009.*","",filename)
    corpus = re.sub("-\dgram.*","",corpus)
    corpus = re.sub("googlebooks-","",corpus)
    print corpus
    i = 0
    for line in reading:
        i = i+1
        if (i==1000000*round(i/1000000)):
            print "reading line no. \t" + str(round(i)/1000000) + " million out of c. 50 million"
        try:
            output = line.split("\t")
            try:
                year = int(output[1])
            except:
                continue
            word = output[0]
            count= output[2]
            string = " ".join([word,count])
            try:
                towrite[year].append(string)
            except:
                towrite[year] = [string]
        except:
            pass
    for year in towrite.keys():
        print year
        if re.search("2gram",filename):
            print corpus
            print str(year)
            writing = open("../../../texts/bigrams/" + corpus+str(year)+".txt",'a')
        elif re.search("1gram",filename):
            writing = open("../../../texts/unigrams/" + corpus+str(year)+".txt",'a')
        else:
            writing = open("tmp/scratch",'a')
        writing.write('\n'.join(towrite[year]))
        writing.close()
