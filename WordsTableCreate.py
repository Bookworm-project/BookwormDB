#!/usr/bin/python
import os
import sys
import re
import subprocess
import codecs
from codecs import open as codecopen


def WordsTableCreate(maxDictionaryLength=1000000, maxMemoryStorage=20000000):
    wordcounts = dict()
    filenum = 1
    readnum = 0
    logfile = open('log.log', 'w')
    database = open('../texts/wordlist/raw.txt', 'w')
    
    for thisfile in os.listdir('../texts/textids'):
        for line in open('../texts/textids/%s' % thisfile, 'r'):
            filenum = filenum + 1
            filename = line.split('\t')[1]
            filename = filename.replace('\n', '')
            try:
                reading = codecopen('../texts/unigrams/%s.txt' % filename, encoding='UTF-8')
                readnum = readnum + 1
                logfile.write('%s %s\n' % (str(readnum), filename))

                for wordEntry in reading:
                    wordEntry = wordEntry.split(' ')
                    if len(wordEntry) > 2:
                        wordEntry = [''.join([wordEntry[i] for i in range(len(wordEntry)-1)]), wordEntry[-1]]
                    wordEntry[1] = int(re.sub('\n','',wordEntry[1]))
                    try:
                        wordcounts[wordEntry[0]] += wordEntry[1]
                    except KeyError:
                        #Really long strings without spaces might mess this up.
                        #30 is a reasonable limit, so 64 seems like plenty.
                        if len(wordEntry[0]) < 64:
                            wordcounts[wordEntry[0]] = wordEntry[1]
                        else:
                            pass
                     #Now we need to delete the words that appear below a cutoff that we find dynamically:
            except UnicodeDecodeError:
                #These just happen, and after a certain point I'm sick of tracking down exactly why to preserve some bizzaro character
                #(It's not accents we're losing, it's stranger birds; I think characters outside of the Unicode alphabet entirely, or something like that.)
                pass
            except:
                pass
            if len(wordcounts) > maxMemoryStorage:
                print "exporting to disk at file number %s" % str(filenum)
                for key in wordcounts.iterkeys():
                    database.write('%s %s\n' % (key.encode('utf-8'), str(wordcounts[key])))
                wordcounts = dict()
                print "export done"

    #dump vocab for the last time when it hasn't reached the limit.
    print "exporting remaining words at file number %s" % str(filenum)
    for key in wordcounts.iterkeys():
        database.write('%s %s\n' % (key.encode('utf-8'), str(wordcounts[key])))

    database.close()

    print("Sorting full word counts\n")
    #This LC_COLLATE here seems to be extremely necessary, because otherwise alphabetical order isn't preserved across different orderings.
    subprocess.call(["export LC_COLLATE='C'; sort -k1 ../texts/wordlist/raw.txt > ../texts/wordlist/sorted.txt"], shell=True)
    
    print("Collapsing word counts\n")
    subprocess.call(["""
         perl -ne '
           BEGIN {use bignum; $last=""; $count=0} 
           if ($_ =~ m/(.*) (\d+)/) {
            if ($last ne $1 & $last ne "") {
             print "$last $count\n"; $count = 0;
            } 
           $last = $1;
           $count += $2
           } END {print "$last $count\n"}' ../texts/wordlist/sorted.txt > ../texts/wordlist/counts.txt"""], shell=True) 
    subprocess.call(["sort -nrk2 ../texts/wordlist/counts.txt > ../texts/wordlist/complete.txt"], shell=True)
    logfile.write("Including the old words first\n")
    oldids = set()
    oldids.add(0)
    oldwords = dict()
    """
    This following section may be fixed for unicode problems
    """
    try:
        i = 1
        oldFile = codecopen("../texts/wordlist/wordlist.txt")
        for line in oldFile:
            line = line.split('\t')
            wid = int(line[0])
            word = line[1]
            oldids.add(wid)
            oldwords[word] = wid
            i = i + 1
            if i > maxDictionaryLength:
                oldFile.close()
                return
        oldFile.close()
    #To work perfectly, this would have to keep track of all the words that have been added, and also update the database with the counts from the old books for each of them. That's hard. Currently, a new word will be added if the new set of texts AND the old one has it in its top 1m words; BUT it will be only added into the database among the new texts, not the old ones. In a few cases defeats the point of updating the old list at all, since we can't see the origins, but at least new people will show up eventually.
    except:
        logfile.write(" No original file to work from: moving on...\n")
    newWords = set()
    logfile.write("writing new ids\n")
    newlist = codecopen("../texts/wordlist/complete.txt")
    i = 1
    nextIDtoAssign = max(oldids) + 1
    counts = list()
    for line in newlist:
        try:
            line = line.split(" ")
            word = line[0]
            count = line[1]
            try:
                wordid = oldwords[word]
            except KeyError:
                wordid = nextIDtoAssign
                nextIDtoAssign = nextIDtoAssign+1
            counts.append("\t".join([str(wordid), word.encode("utf-8"), count]))
            i = i + 1
            if i > maxDictionaryLength:
                break
        except:
            pass
    output = open("../texts/wordlist/newwordlist.txt", "w")
    for count in counts:
        output.write(count) #Should just carry over the newlines from earlier.
    
    #Don't overwrite the new file until the old one is complete
    subprocess.call(["mv", "../texts/wordlist/newwordlist.txt", "../texts/wordlist/wordlist.txt"])

if __name__ == "__main__":
    WordsTableCreate(maxDictionaryLength=1000000, maxMemoryStorage=15000000)
