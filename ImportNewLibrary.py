#!/usr/bin/python
#Currently only doing the last few stages!
import subprocess
from subprocess import call as sh
import os
"""
We start with files at, relative to the main presidio directory:

../texts/raw      The raw text files.  The files themselves should be named
                  'stringidentifier.txt' and the ids 'stringidentifier' should be
                  listed in a textids/ file.

../texts/textids  Any number of text files that each consist of a numeric and a 
                  stringidentifier (the numeric identifier is just an incrementing
                  integer guaranteed to be unique across the full dataset).  This
                  should be tab-delimited and should exclude the ".txt" extension.

Example creation of one such text file, run from ../texts/raw: (this would run better with "find" than "ls" in practice)

ls *.txt | awk -F '.txt' '{count++; print count "\t" $1;}' > ../textids/cat0001.txt

The easiest form of parallelization at the moment is just to shift around the 
number of files in each location at /texts/textfiles. This allows the use of multiple processors.
Adding more locations with knowledge onlyof a few files would allow easy multi-machine parallelization as well.

"""

#There are a whole bunch of directories that it wants to be there:
for directory in ['texts','logs','texts/cleaned','logs','logs/clean','texts/unigrams','logs/unigrams','logs/bigrams','texts/bigrams','texts/encoded','texts/encoded/unigrams','texts/encoded/bigrams','logs/encode2','logs/encode1', 'texts/wordlist']:
    if not os.path.exists("../" + directory):
        sh(['mkdir', '../' + directory])

"""Use the cleaning program to make texts that are set for tokenizing, and with sentences at linebreaks."""
print "Cleaning the texts"
#sh(['python','master.py','clean'])
print "Creating 1 gram counts"
#sh(['python','master.py','unigrams'])
print "Creating 2gram counts"
#sh(['python','master.py','bigrams'])

print "Would be creating 3gram counts..."
#Just kidding, this isn't implemented
print "Creating a master wordlist"
sh(['python','WordsTableCreate.py'])
#We could add an option to this to specify the size of the dictionary used. Currently hardcoded at 3,000,000 words. 
#On very large dictionaries, this may crash for lack of memory on machines with insufficient RAM; the script is an obvious candidate for map-reduce.

#These tend to be the most time-intensive scripts, since they involve a lot of dictionary lookups
print "Creating 1grams encodings"
sh(['python','master.py','encode1'])

print "Creating 2grams encodings"
sh(['python','master.py','encode2'])
