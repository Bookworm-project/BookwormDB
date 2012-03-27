#!/usr/bin/python

import os
import sys
import re
maxDictionaryLength=2000000

wordcounts = dict()

for file in os.listdir('../texts/textids'):
    for line in open('../texts/textids/' + file,'r'):
        filename = line.split('\t')[1]
        filename = re.sub('\n','',filename)
        try:
            reading = open('../texts/unigrams/'+filename+'.txt')
            for wordEntry in reading:
                wordEntry = wordEntry.split(' ')
                wordEntry[1] = int(re.sub('\n','',wordEntry[1]))
                try:
                    wordcounts[wordEntry[0]]+=wordEntry[1]
                except KeyError:
                    wordcounts[wordEntry[0]] = wordEntry[1]
#Now we need to delete the words that appear below a cutoff that we find dynamically:
                countcounts = dict()
        except:
            print "Error on WordsTableCreate: could not find file " + filename + "\n"
for key in wordcounts:
    try:
        countcounts[wordcounts[key]] += 1
    except KeyError:
        countcounts[wordcounts[key]] = 1

ticker = 0
#cutoff is the 
minimumCountsForInclusion = 1 
for key in sorted(countcounts.keys(),reverse=True):
    ticker += countcounts[key]
#    print str(key) + ' has ' + str(countcounts[key]) + ' types of things ticker is at ' + str(ticker)
    if ticker > maxDictionaryLength:
        minimumCountsForInclusion = key
        break

for key in wordcounts.keys():
    if wordcounts[key] < minimumCountsForInclusion:
        del wordcounts[key]

OUTFILE = open("../texts/wordlist/wordlist.txt",'w')

wordid = 0
for word in sorted(wordcounts,key=wordcounts.get,reverse=True):
    wordid = wordid + 1
    OUTFILE.write(str(wordid) + '\t' + word + '\t' + str(wordcounts[word]) + '\n')
