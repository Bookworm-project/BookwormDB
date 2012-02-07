#!/usr/bin/python

import subprocess
from subprocess import call as sh
import os
"""
We start with files at, relative to the main presidio directory:
../texts/textfiles (Any number of text files that each consist of a numeric and a stringidentifier (the numeric identifier is just an incrementing integer guaranteed to be unique across the full dataset.
../texts/raw (The files themselves will be named 'stringidentifier.txt')
The easiest form of parallelization at the moment is just to shift around the number of files in each location at /texts/textfiles, and possibly to create several different locations.
"""

#There are a whole bunch of directories that it wants to be there:
for directory in ['texts','logs','texts/cleaned','logs','logs/clean','texts/unigrams','logs/unigrams','logs/bigrams','texts/bigrams','texts/encoded','texts/encoded/unigrams','texts/encoded/bigrams','logs/encode2','logs/encode1']:
    if not os.path.exists("../" + directory):
        sh(['mkdir', '../' + directory])

"""Use the cleaning program to make texts that are set for tokenizing, and with sentences at linebreaks."""
print "Cleaning the texts"
sh(['python','master.py','clean'])
print "Creating 1 gram counts"
sh(['python','master.py','unigrams'])
print "Creating 2gram counts"
sh(['python','master.py','bigrams'])
#We could add 3grams, and so forth, here.

print "Creating a master wordlist"
sh(['python','WordsTableCreate.py'])
#We could add an option to this to specify the size of the dictionary used. Currently hardcoded at 3,000,000 words. On very large dictionaries, this may crash for lack of memory; the script is an obvious candidate for map-reduce.

print "Creating 1grams encodings"
sh(['python','master.py','encode1'])

print "Creating 2grams encodings"
sh(['python','master.py','encode2'])
