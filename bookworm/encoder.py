#!/usr/bin/python
from tokenizer import *
import os
import cPickle as pickle
import sys

def encodeFiles(array):
    IDfile = readIDfile()
    dictionary = readDictionaryFile()
    for thisfile in array:
        print thisfile
        input = pickle.load(open(thisfile))
        for level in input.levels:
            input.encode(level,IDfile,dictionary)


if __name__=="__main__":
    encodeFiles(sys.argv[1:])
