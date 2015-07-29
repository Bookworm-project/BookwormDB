#!/usr/bin/python
from tokenizer import *
import os
import cPickle as pickle
import sys
import re

def encodeFiles(array):
    IDfile = readIDfile()
    dictionary = readDictionaryFile()
    for thisfile in array:
        try:
            input = pickle.load(open(thisfile))
        except ValueError:
            logging.warn("unable to unpicked " + thisfile + "... dangerously just " + \
                "skipping, some texts may be lost")
            continue
        except:
            logging.warn("Some problem: fix if " + thisfile + " should be unpicklable")
            continue
        for level in input.levels:
            input.encode(level,IDfile,dictionary)


if __name__=="__main__":
    passedList = sys.argv[1:]
    toEncode = []
    for file in passedList:
        basename = re.sub(".*/","",file)
        if not os.path.exists(".bookworm/texts/encoded/unigrams/"+basename + ".txt"):
            if not os.path.exists(".bookworm/texts/encoded/bigrams/"+basename + ".txt"):
                toEncode.append(file)
    logging.info("preparing to encode " + str(len(toEncode)) + " files" + " out of " + \
        str(len(passedList)))
    encodeFiles(toEncode)
