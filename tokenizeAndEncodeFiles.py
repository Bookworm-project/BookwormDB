#!/usr/bin/python

import os
import subprocess
import multiprocessing
import re

"""
I want to use multiprocessing to actually spawn real child processes: this is replacing the old file
master.py to do that.
"""

#Because pools don't work with class methods: #http://bytes.com/topic/python/answers/552476-why-cant-you-pickle-instancemethods
#and because multiprocessing pools don't allow multiple methods.

def noShellCall(arg):
    subprocess.call(arg,shell=False)

def shellCall(arg):
    subprocess.call(' '.join(arg),shell=True)
    
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
        self.processors = multiprocessing.cpu_count()*2 #Try double for some Intel processors: can't hurt much, right?
        #We can accept at most 100K arguments at a time on the command line.
        #but varies from system to system. So break up the chunks into lots and lots of pieces.
        self.processes = max([self.processors,int(len(self.bookids)/10000)])
        #and make it divisible by the number of processors which should help make it go optimally fast.
        #(although it should maybe be down to n-1 or something, in case one thread is hanging or one is super-speedy)
        self.processes = int(self.processes/self.processors)*self.processors + self.processors
        self.booklists = [bookids[i::self.processes] for i in range(self.processes)]

    def encode(self,mode):
        #mode is 'unigrams' or 'bigrams' (or trigrams)
        #This just takes the raw file, the perl script knows where to look.
        #Not the cleanest.
        self.args = [['perl','encodeText.pl',mode] + booklist for booklist in self.booklists]

    def tokenize(self,mode):
        if mode=='trigrams':
            n=3
        if mode=='bigrams':
            n=2
        if mode=='unigrams':
            n=1
        if not mode in ('unigrams','bigrams','trigrams'):
            print "must specify mode of 'unigrams' or 'bigrams'" 
            raise
        self.args=[]
        for bookid in self.bookids:
            bookinstance = book(bookid)
            bookinstance.ngrams(n)
            myArg = bookinstance.generateArgument()
            if len(myArg)>0: #many cases this will return empty
                self.args.append(myArg)
        self.execute(exMethod=shellCall)
        print "Done Tokenizing"

    def clean(self):
        self.args=[]
        for bookid in self.bookids:
            bookinstance=book(bookid)
            bookinstance.clean()
            myArg = bookinstance.generateArgument()
            if len(myArg)>0: #many cases this will return empty
                self.args.append(myArg)
        self.execute(exMethod=shellCall)
        print "Done cleaning"

    def encodeUnigrams(self):
        self.encode('unigrams')
        self.execute()

    def encodeBigrams(self):
        self.encode('bigrams')
        self.execute()

    def encodeTrigrams(self):
        self.encode('bigrams')
        self.execute()

    def execute(self,exMethod=noShellCall):
        pool = multiprocessing.Pool(processes=self.processors)
        pool.map(exMethod,self.args)

class book:
    #This class takes a bookid. The first call is the method to prep (encode2,onegrams, etc); it creates an attribute self.execute() which can then be called to write the next file in the chain.
    #Ideally these could be linked together more flexibly than they are here to do multiple operations on a book at once in memory.
    #The different operations are cast in terms of pipes, because the basic stemming and tokenizing scripts are written mostly in perl and awk, not python
    #They are easy enough to call from the command line. 
    def __init__(self,bookid):
        self.bookid = bookid
        self.coreloc = bookid + ".txt"
        
    def ngrams(self,n):
        #This generalizes writing an awk script to pull out gram counts
        #The join loop here prints a string like '$(i+0) " " $(i+1) " " $(i+2)' that gets the words in position i to i+2 plus two as a group for the thing to use. 
        #At some point 'unigrams' and 'bigrams' should be deleted as methods, and only this should be used.
        self.start_operator = "cat"
        self.start = "../texts/cleaned/" + self.coreloc
        self.function = """awk '{ for(i=1; i<NF-""" +str(n-1)+ """; i++)                    
                 {count[""" + ' " " '.join(["$(i+" + str(j) + ")" for j in range(0,n)]) + """]++}
                 }
                 END{          
                 for(i in count){print i, count[i]}}'"""
        destinations = {1:"unigrams",2:"bigrams",3:"trigrams",4:"quadgrams",5:"quintgrams"}
        self.destination = "../texts/"+destinations[n] +"/" + self.coreloc

        #self.execute   = self.shell_execute
                 
    def clean(self):
        self.start_operator = "cat"
        self.start = "../texts/raw/" + self.coreloc
        self.function = "perl CleanText.pl"
        self.destination = "../texts/cleaned/" + self.coreloc
        #self.execute = self.shell_execute

    def generateArgument(self):
        if os.path.exists(self.destination):
            #print "No action. "+self.destination+" already exists."
            return []
        if not os.path.exists(self.start):
            print "No action. "+self.start+" does not exist."
            return []
        if os.path.getsize(self.start) < 10:
            print "No action. "+self.start+" is too small."
            return []
        #print "working on " + self.bookid
        shell_operators = [self.start_operator,self.start,"|",self.function,">",self.destination]
        return(shell_operators)

if __name__ == '__main__':
    bookids = bookidlist()
