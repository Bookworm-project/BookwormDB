#!/usr/bin/python

import re
import os
import sys
import time
import threading
import thread
import random
import subprocess
from subprocess import Popen
from subprocess import PIPE
from subprocess import call
import urllib
start = time.time()
'''
Our work on the big server involves applying lots of work to a large number of 
texts. These processes are heavily parallelizable; this is a wrapper that does most 
of the work of splitting up the textlists into multiple chunks, and then applying a 
function across all of them. The code itself is usually trivial, but the different 
steps are good to keep around at different points. (We want the same files to create
3-grams and 2-grams from, say, or it's good to have English frequency counts as 
well as encoded ones in case the encoding changes.

The basic parallelization is built around splitting up the list of input files into 
chunks of 100,000 texts each. (Maybe not the most elegant solution, but it works 
fine for now.)
'''
#PASS THE MODE THROUGH THE COMMAND LINE
try:
    mode = sys.argv[1]
except:
    print "This probably won't work without an argv value, but we'll let you try."
    mode = None
    
class bookids_file:
    def __init__(self,targetfile,mode,auxdata = ""):
        #auxdata is a weird structure so I can pass bookid files or whatever else is needed to the instances.
        print "Processing texts in "+targetfile+"\n"
        self.targetfile = targetfile
        self.mode = mode
        self.reset_writefiles()
        self.auxdata = auxdata
    def reset_writefiles(self):
        self.textsfile = open("../texts/textids/" + self.targetfile,'r')
        self.LOGFILE = open("../logs/" + self.mode + "/" + self.targetfile + ".log",'w')
    def execute(self):
        print "Performing "+mode+"\n"
        i = 0
        for line in self.textsfile:
            splitted = line.split("\t")
            intid = splitted[0]
            bookid = splitted[1]
            bookid = re.sub("\n","",bookid)
            bookid = re.sub(" ","",bookid)
            if len(bookid) > 0:
                i = i+1
                self.LOGFILE.write(str(i) + " " + bookid + " " + str(round(time.time()-start,2)) + "\n")
                mybook = book(bookid,self.LOGFILE,self.auxdata)
                getattr(mybook,self.mode)()
                try:
                    mybook.execute()
                except:
                    print "Error on " + bookid + " "
                    raise



class book:
    #This class takes a bookid. The first call is the method to prep (encode2,onegrams, etc); it creates an attribute self.execute() which can then be called to write the next file in the chain.
    #Ideally these could be linked together more flexibly than they are here to do multiple operations on a book at once in memory.
    #The different operations are cast in terms of pipes, because the basic stemming and tokenizing scripts are written mostly in perl and awk, not python
    #They are easy enough to call from the command line.
    def __init__(self,bookid,LOGFILE,auxdata=""):
        self.bookid = bookid
        self.coreloc = bookid + ".txt"
        self.LOGFILE = LOGFILE
        self.auxdata = auxdata
    def encode2(self):
        self.start = "../texts/bigrams/" + self.coreloc
        self.destination = "../texts/encoded/bigrams/" + self.coreloc
        self.execute = self.encode
    def encode1(self):
        self.start = "../texts/unigrams/" + self.coreloc
        self.destination = "../texts/encoded/unigrams/" + self.coreloc
        self.execute = self.encode
    def upload(self):
        db.query("LOAD DATA INFILE")
    def encode(self):
        #This works for any number of ngrams as an input file.
        self.wordids = self.auxdata
        if not os.path.exists(self.start):
            return
        if os.path.exists(self.destination):
            return
        if os.path.getsize(self.start) < 10:
            return
        countfile = open(self.start,'r')
        writefile = open(self.destination,'w')
        lines = [] #Keep all the lines in memory--I think this is faster than moving the disk head around after each line.
        for line in countfile:
            line = line.split(" ")
            try:
                for i in range(len(line)-1):
                    line[i] = self.wordids[line[i]]
            except KeyError:
                continue #So if one of the words isn't include, we move on: another option would be to write an 'unknown' or something.
            lines.append("\t".join(line))
            #This little 'append' here and then 'write' later loop seems like it's probably the fastest way to do this in Python; at least, it isn't slow.
        writefile.write("".join(lines))
    def unigrams(self):
        self.start_operator = "cat"
        self.start = "../texts/cleaned/" + self.coreloc
        self.function = """awk '{ for(i=1; i<NF; i++)
        {count[$i]++}
        }
        END{
        for(i in count){print i, count[i]}
        }'"""
        self.destination = "../texts/unigrams/" + self.coreloc
        self.execute = self.shell_execute
    def bigrams(self):
        self.start_operator = "cat"
        self.start = "../texts/cleaned/" + self.coreloc
        self.function = """awk '{ for(i=1; i<NF-1; i++)
                                  {count[$i " " $(i+1)]++}
                                  }
                                 END{
                                  for(i in count){print i, count[i]}}'"""
        self.destination = "../texts/bigrams/" + self.coreloc
        self.execute     = self.shell_execute
    def ngrams(self,n):
        #This generalizes writing an awk script to pull out gram counts
        #The join loop here prints a string like '$(i+0) " " $(i+1) " " $(i+2)' that gets the words in position i to i+2 plus two as a group for the thing to use.
        self.start_operator = "cat"
        self.start = "../texts/cleaned/" + self.coreloc
        self.function = """awk '{ for(i=1; i<NF-""" +str(n-1)+ """; i++)
                                  {count[""" + ' " " '.join(["$(i+" + str(j) + ")" for j in range(0,n)]) + """]++}
                                  }
                                 END{
                                  for(i in count){print i, count[i]}}'"""
        self.destination = "../texts/bigrams/" + self.coreloc
        self.execute     = self.shell_execute
    def clean(self):
        self.start_operator = "cat"
        self.start = "../texts/raw/" + self.coreloc
        self.function = "perl CleanText.pl"
        self.destination = "../texts/cleaned/" + self.coreloc
        self.execute = self.shell_execute
    def shell_execute(self):
        if os.path.exists(self.destination):
            self.LOGFILE.write("No cleaning. "+self.destination+" already exists.\n")
            return
        if not os.path.exists(self.start):
            self.LOGFILE.write("No cleaning. "+self.start+" does not exist.\n")
            return
        if os.path.getsize(self.start) < 10:
            self.LOGFILE.write("No cleaning. "+self.start+" is too small.\n")
            return
        self.LOGFILE.write("working on " + self.bookid)
        shell_operators = [self.start_operator,self.start,"|",self.function,">",self.destination]
        results = subprocess.call([" ".join(shell_operators)],shell=True,stderr=subprocess.STDOUT)
            
class bookids_Instance(threading.Thread):
    def __init__(self,targetfile,mode,auxdata = ""):
        threading.Thread.__init__(self)
        self.targetfile=targetfile
        self.mode = mode
        self.auxdata = auxdata
    def run(self):
        bookids_group = bookids_file(self.targetfile,self.mode,auxdata = self.auxdata)
        bookids_group.execute()

def get_wordids():
    wordids=dict()
    i = 0
    wordsfile = open("../texts/wordlist/wordlist.txt")
    for myline in wordsfile:
        myline = re.sub("\n","",myline)
        myline = myline.split("\t")
        wordids[myline[1]] = myline[0];
        i += 1
        if i >= 1000000:
            print "done reading in files."
            return wordids
    return wordids

if re.search("encode",mode):
    print "Getting wordids from file"
    wordids = get_wordids()

filelists = os.listdir("../texts/textids")

for filelist in filelists:
    if re.search("encode",mode):
        instance = bookids_Instance(filelist,mode,auxdata=wordids)
    else:
        instance = bookids_Instance(filelist,mode)
    instance.start()

#This bit here keeps the program from shutting down until all the threads are done.
while threading.activeCount()>1:
    time.sleep(2)
        
