#!/usr/bin/python

from tokenizer import *
import sys
import subprocess
import timeit

def exportToDisk(wordcounts,diskFile,keepThreshold=5):
    commonwords = dict()
    for key in wordcounts.iterkeys():
        if wordcounts[key] < keepThreshold:
            key = key
            output = key + " " + str(wordcounts[key]) + "\n"
            diskFile.write(output)
        else:
            commonwords[key] = wordcounts[key]
    return commonwords
    print "export done"
    
def WordsTableCreate(maxDictionaryLength=1000000, maxMemoryStorage=20000000):
    database = open('files/texts/wordlist/raw.txt','w')
    start_time = timeit.default_timer()
    n = 1
    #When flushing the dictionary to disk, they are kept in memory if there count is
    #greater than keepThreshold to avoid overhead reinitializing and rewriting.
    keepThreshold=2

    wordcounts = dict()
    for row in sys.stdin:
        for item in row.split(" "):
            n+=1
            if n % 10000000==0:
                elapsed = timeit.default_timer() - start_time
                print str(len(wordcounts)) + " entries at " + str(n) + " words---" + str(elapsed) + " seconds since last print"
                start_time = timeit.default_timer()
            item = item.rstrip("\n")
            try: 
                wordcounts[item] += 1
            except KeyError:
                wordcounts[item] = 1

            while len(wordcounts) > maxMemoryStorage:
                print "exporting to disk..."
                wordcounts = exportToDisk(wordcounts,diskFile=database,keepThreshold=keepThreshold)
                if len(wordcounts) > maxMemoryStorage:
                    #If that's not enough to get down to a small dictionary,
                    #try again with a new higher limit.
                    keepThreshold = keepThreshold*2

    #Write all remaining items to disk
    nothing = exportToDisk(wordcounts,diskFile=database,keepThreshold=float("inf"))
    database.close()
    sortWordlist(maxDictionaryLength=maxDictionaryLength)

def sortWordlist(maxDictionaryLength=1000000):

    print("Sorting full word counts\n")
    #This LC_COLLATE here seems to be extremely necessary, because otherwise alphabetical order isn't preserved across different orderings.
    subprocess.call(["export LC_COLLATE='C';export LC_ALL='C'; sort -k1 files/texts/wordlist/raw.txt > files/texts/wordlist/sorted.txt"], shell=True)
    
    print("Collapsing word counts\n")
    
    #This is in perl, using bignum, because it's possible to get integer overflows on a really huge text set (like Google ngrams).

    subprocess.call(["""
           perl -ne '
           BEGIN {use bignum; $last=""; $count=0} 
           if ($_ =~ m/(.*) (\d+)/) {
            if ($last ne $1 & $last ne "") {
             print "$last $count\n"; $count = 0;
            } 
           $last = $1;
           $count += $2
           } END {print "$last $count\n"}' files/texts/wordlist/sorted.txt > files/texts/wordlist/counts.txt"""], shell=True) 

    subprocess.call(["export LC_ALL='C';export LC_COLLATE='C';sort -nrk2 files/texts/wordlist/counts.txt > files/texts/wordlist/complete.txt"], shell=True)
    # logfile.write("Including the old words first\n")
    oldids = set()
    oldids.add(0)
    oldwords = dict()

    """
    This following section may be fixed for unicode problems
    """

    try:
        i = 1
        oldFile = open("files/texts/wordlist/wordlist.txt")
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

    #To work perfectly, this would have to keep track of all the words that have been added, and also update the database with the counts from the old books for each of them. That's hard. Currently, a new word will be added if the new set of texts AND the old one has it in its top 1m words; BUT it will be only added into the database among the new texts, not the old ones. In a few cases that defeats the point of updating the old list at all, since we can't see the origins, but at least new people will show up eventually.
    except:
        # logfile.write(" No original file to work from: moving on...\n")
        pass
    newWords = set()
    # logfile.write("writing new ids\n")
    newlist = open("files/texts/wordlist/complete.txt","r")
    i = 1
    nextIDtoAssign = max(oldids) + 1
    counts = list()
    for line in newlist:
        line = line.split(" ")
        word = line[0]
        count = line[1]
        try:
            wordid = oldwords[word]
        except KeyError:
            wordid = nextIDtoAssign
            nextIDtoAssign = nextIDtoAssign+1
        counts.append("\t".join([str(wordid), word, count]))
            
        i = i + 1
        if i > maxDictionaryLength:
            break

    output = open("files/texts/wordlist/newwordlist.txt", "w")
    for count in counts:
        output.write(count) #Should just carry over the newlines from earlier.
    
    #Don't overwrite the new file until the old one is complete
    subprocess.call(["mv", "files/texts/wordlist/newwordlist.txt", "files/texts/wordlist/wordlist.txt"])



if __name__=="__main__":
    WordsTableCreate()

