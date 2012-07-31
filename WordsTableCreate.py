#!/usr/bin/python

import os
import sys
import re
import subprocess
from subprocess import call

maxDictionaryLength=2000000
#10 million words should be about 1 gigabyte of memory, which is plenty on the servers we use: flush out every time we hit that limit.
maxMemoryStorage = 10000000
wordcounts = dict()
filenum = 1
readnum = 0
logfile = open("log.log",'w')
database = open("../texts/wordlist/raw.txt",'w')


for file in os.listdir('../texts/textids'):
    for line in open('../texts/textids/' + file,'r'):
        filenum = filenum + 1
        filename = line.split('\t')[1]
        filename = re.sub('\n','',filename)
        try:
            readnum = readnum+1
            #logfile.write(str(readnum) + " " + filename)
            reading = open('../texts/unigrams/'+filename+'.txt')
            for wordEntry in reading:
                wordEntry = wordEntry.split(' ')
                wordEntry[1] = int(re.sub('\n','',wordEntry[1]))
                try:
                    wordcounts[wordEntry[0]]+=wordEntry[1]
                except KeyError:
                    #Really long strings without spaces might mess this up.
                    #30 is a reasonable limit, so 64 seems like plenty.
                    if len(wordEntry[0]) < 64:
                        wordcounts[wordEntry[0]] = wordEntry[1]
                    else:
                        pass
#Now we need to delete the words that appear below a cutoff that we find dynamically:
                countcounts = dict()
        except:
            pass
            #print "Error on WordsTableCreate: could not find file " + filename + " (...moving on to next file...)"
        if len(wordcounts) > maxMemoryStorage:
            print "exporting to disk at file number " + str(filenum)
            keys = wordcounts.keys()
            for key in keys:
                database.write(key + " " + str(wordcounts[key])+"\n")
            wordcounts=dict()
            print "  export done"

keys = wordcounts.keys()
for key in keys:
    database.write(key + " " + str(wordcounts[key]) + "\n")

#dump vocab for the last time when it hasn't reached the limit.

database.close()

print("Sorting full word counts\n")
#This LC_COLLATE here seems to be extremely necessary, unfortunately for sanity's sake.
call(["export LC_COLLATE='C'; sort -k1 ../texts/wordlist/raw.txt > ../texts/wordlist/sorted.txt"],shell=True)
print("Collapsing word counts\n")
call(["""awk 'BEGIN{count=0}
        {
         if (NR==1)
            {count=0;word=$1;}
         if ($1==word)
            count += $2
         if ($1!=word) {
            print word " " count;
            word=$1;
            count=$2;
            }
        } END {print word " " count;}
        ' ../texts/wordlist/sorted.txt > ../texts/wordlist/counts.txt"""],shell=True) 


call(["""sort -nrk2 ../texts/wordlist/counts.txt > ../texts/wordlist/complete.txt"""],shell=True)
logfile.write("Adding rank numbers to the usable ones")


#To get this working with already entered lists of words, this idea should be implemented: (it could also work from the raw file)
#CALL DATABASE RESULTS:

#FOR EACH, ADD word->key to dictionary:

#Read in the top maxDictionaryLength items from the new list:

#Add new entries for any words in that list that aren't in the new one.

#write out to ../texts/wordlist/wordlist.txt



call(["""head -""" + str(maxDictionaryLength) + """ ../texts/wordlist/complete.txt | awk '{print NR "\t" $1 "\t" $2}' > ../texts/wordlist/wordlist.txt """],shell=True)  

