#!/usr/bin/python

import os
import sys
import re
import subprocess
from subprocess import call
maxDictionaryLength=2000000
#10 million words should be about 1 gigabyte of memory, which is plenty on the servers we use: flush out every time we hit that limit.
maxMemoryStorage = 40000000
wordcounts = dict()
filenum = 1
readnum = 0
logfile = open("log.log",'w')

try:
    call(['mkdir','../texts/wordlist/tmp'])
except:
    print "Error on mkdir: is it already there?"

for file in os.listdir('../texts/textids'):
    for line in open('../texts/textids/' + file,'r'):
        filename = line.split('\t')[1]
        filename = re.sub('\n','',filename)
        try:
            readnum = readnum+1
            print str(readnum) + " " + filename
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
            print "Error on WordsTableCreate: could not find file " + filename + "\n"
        if len(wordcounts) > maxMemoryStorage:
            logfile.write("Creating tmp table number " + str(filenum) + " (" + str(readnum) + "books)\n")
            file = open('../texts/wordlist/tmp/'+str(filenum) + '.txt','w')
            filenum=filenum+1
            keys = wordcounts.keys()
            keys.sort()
            for key in keys:
                file.write(key+"\t"+str(wordcounts[key])+"\n")
            wordcounts=dict()

#Then use textutils to do all the hard work without having to worry about memory management.

#Do it again on the leftovers.
file = open('../texts/wordlist/tmp/'+str(filenum) + '.txt','w')
keys = wordcounts.keys()
keys.sort()
for key in keys:
    file.write(key+"\t"+str(wordcounts[key])+"\n")

logfile.write("merging tmpfiles\n")

if filenum == 1:
    args = ["cat","../texts/wordlist/tmp/1.txt"]

if filenum > 1:
    args = ["join","-a1","-a2","../texts/wordlist/tmp/1.txt","../texts/wordlist/tmp/2.txt"]

if filenum > 2:
    for i in range(3,filenum+1):
    #Each join is piped to the next file in the chain to do them all at once:
        for string in ["|","join","-a1","-a2","-","../texts/wordlist/tmp/" + str(i)+".txt"]:
            args.append(string)

args.append(">")
args.append("../texts/wordlist/tmp/countnums.txt")
print "Running code snippet of -- " + " ".join(args)

call(" ".join(args),shell=True)

logfile.write("tmpfiles merged; getting full word counts\n")

call(["""
awk '
BEGIN {FS=" ";OFS="\t"}
{
sum=0;
for(i=2;i<=NF;i++)
     {sum+=$i}
     print $1 "\t" sum}' ../texts/wordlist/tmp/countnums.txt > ../texts/wordlist/counts.txt"""],shell=True) 

logfile.write("Sorting full word counts\n")
call(["""sort -nrk2 ../texts/wordlist/counts.txt > ../texts/wordlist/complete.txt"""],shell=True)
logfile.write("Adding rank numbers to the usable ones")
call(["""head -""" + str(maxDictionaryLength) + """ ../texts/wordlist/complete.txt | awk '{print NR " " $0}' > ../texts/wordlist/wordlist.txt """],shell=True)  

