#!/usr/bin/python

import subprocess
import os

#There are a whole bunch of directories that it wants to be there:
for directory in ['texts','logs','texts/cleaned','logs','logs/clean','texts/unigrams','logs/unigrams','logs/bigrams','texts/bigrams','texts/encoded','texts/encoded/unigrams','texts/encoded/bigrams','logs/encode2','logs/encode1', 'texts/wordlist']:
    if not os.path.exists("../" + directory):
        subprocess.call(['mkdir', '../' + directory])

def CopyDirectoryStructuresFromRawDirectory():
    #Internal python solutions for this are not as fast or as clean as simply using rsync in the shell.
    #That's what the code below does. Downside: it requires rsync.
    print "Copying directory Structures from primary folder to later ones..."
    subprocess.call(["sh","./scripts/copyDirectoryStructures.sh"])