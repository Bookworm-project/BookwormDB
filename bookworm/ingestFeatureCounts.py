import os
import subprocess
import sys
from tokenizer import *

# This script reads in a unigrams file that must be formatted
# as "textid, token, count."

# If you want to force comma-delimited or tab-delimited splitting (instead of the current
# whitespace splitting), change this variable.
sep=None


# For now, you have to create these files. (I'd recommend doing it as a named pipe)

unigrams = "../unigrams.txt"
bigrams = "../bigrams.txt"

# Bookwormdir is defined in the call.



def writeWordIDs():
    """
    The wordids are counted directly from the unigrams file.
    """
    
    output = open("files/texts/wordlist/wordlist.txt","w")
    global sep
    wordcounts = dict()
    for line in open(unigrams):
        (bookid,word,count) = line.split(sep)
        count = int(count)
        try:
            wordcounts[word] += count
        except KeyError:
            wordcounts[word] = count
    tuples = [(v,k) for k,v in wordcounts.iteritems()]
    tuples.sort()
    tuples.reverse()
    wordid = 0
    for (count,word) in tuples:
        wordid += 1
        output.write("\t".join([str(wordid),word,str(count)]) + "\n")


if sys.argv[1]=="wordIds":
    writeWordIDs()


if sys.argv[1]=="encode":
    encodePreTokenizedStream(open("../unigrams.txt"),levels=["unigrams"])
    #encodePreTokenizedStream(open("../bigrams"),levels=["bigrams"])
