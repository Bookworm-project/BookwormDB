#!/usr/bin/python

import os
import sys
import re
import subprocess
from subprocess import call

def WordsTableCreate(maxDictionaryLength=2000000,maxMemoryStorage = 20000000):
#20 million words should be about 2 gigabyte of memory, which is plenty on the servers we use: flush out every time we hit that limit.

    wordcounts = dict()
    filenum = 1
    readnum = 0
    logfile = open("log.log",'w')
    #I call this 'database' rather than 'wordlist' because it could be a database, so we might as well think of it as one.
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
    #dump vocab for the last time when it hasn't reached the limit.
    keys = wordcounts.keys()
    for key in keys:
        database.write(key + " " + str(wordcounts[key]) + "\n")



    database.close()

    print("Sorting full word counts\n")
    #This LC_COLLATE here seems to be extremely necessary, because otherwise alphabetical order isn't preserved across different orderings.
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
    logfile.write("Including the old words first")

    oldids = set()
    oldids.add(0)
    oldwords = dict()
    """
    This following section needs to be fixed for unicode problems
    """
    import codecs

    try:
        i = 1
        oldFile = open("../texts/wordlist/wordlist.txt")
        for line in oldFile:
            line = line.encode('utf-8')
            line = line.split('\t')
            wid = int(line[0])
            word = line[1]
            oldids.add(wid)
            oldwords[word] = wid
            i = i+1
            if i > maxDictionaryLength:
                oldFile.close()
                return
        oldFile.close()

    #To work perfectly, this would have to keep track of all the words that have been added, and also update the database with the counts from the old books for each of them. That's hard.

    except:
        logfile.write(" No original file to work from: moving on...\n")
    newWords = set()
    logfile.write("writing new ids")
    newlist = open("../texts/wordlist/complete.txt")
    i = 1
    nextIDtoAssign = max(oldids)+1
    counts = list()
    for line in newlist:
        line = line.encode('utf-8')
        line = line.split(" ")
        word = line[0]
        count = line[1]
        try:
            wordid = oldwords[word]
        except KeyError:
            wordid = nextIDtoAssign
            nextIDtoAssign = nextIDtoAssign+1
        counts.append("\t".join([str(wordid),word,count]))
        i = i+1
        if i > maxDictionaryLength:
            return

    output = open("../texts/wordlist/newwordlist.txt", "w")

    for count in counts:
        output.write(count) #Should just carry over the newlines from earlier.

    #Don't overwrite the new file until the old one is complete
    call(["mv", "../texts/wordlist/newwordlist.txt", "../texts/wordlist/wordlist.txt"])
            

    #call(["""head -""" + str(maxDictionaryLength) + """ ../texts/wordlist/complete.txt | awk '{print NR "\t" $1 "\t" $2}' > ../texts/wordlist/wordlist.txt """],shell=True)  

WordsTableCreate(maxDictionaryLength=1000000,maxMemoryStorage = 20000000)
