#!/usr/bin/python

import os
import subprocess
import multiprocessing
import re

"""
I want to use multiprocessing to actually spawn real child processes: this is going to replace
master.py to do that.

For now, only the encoding methods are implemented, because those are where the slowdowns appeared
the most extreme.
"""


class bookidlist:
    def __init__(self):
        filelists = os.listdir("../texts/textids")
        bookids = []
        for filename in filelists:
            for line in open("../texts/textids/" + filename):
                splitted = line.split("\t")
                intid = splitted[0]
                bookid = splitted[1]
                bookid = re.sub("\n","",bookid)
                bookid = re.sub(" ","",bookid)
                bookids.append(bookid)
        self.bookids = bookids

        print "Done reading in files: moving to create subprocesses"
        self.processors = multiprocessing.cpu_count()
        #We can accept at most 100K arguments at a time on the command line.
        self.processes = max([self.processors,int(len(self.bookids)/10000)])
        #and make it divisible by the number of processors which should help make it go optimally fast.
        #(although it should maybe be down to n-1 or something, in case one thread is hanging or one is super-speedy)
        self.processes = int(self.processes/self.processors)*self.processors + self.processors
        self.booklists = [bookids[i::self.processes] for i in range(self.processes)]

    def encode(self,mode):
        #mode is 'unigrams' or 'bigrams'
        self.args = [['perl','encodeText.pl',mode] + booklist for booklist in self.booklists]
        
    def prepArgList(self,method,length=None):
        getattr(self,method)(length)
        
    def encodeUnigrams(self):
        self.prepArgList('encode','unigrams')
        self.execute()

    def encodeBigrams(self):
        self.prepArgList('encode','bigrams')
        self.execute()
        
    def execute(self):
        pool = multiprocessing.Pool(processes=self.processors)
        pool.map(subprocess.call,self.args)

if __name__ == '__main__':
    bookids = bookidlist()
    bookids.prepArgList('encode','unigrams')
    bookids.execute()
    bookids.prepArgList('encode','bigrams')
    bookids.execute()


