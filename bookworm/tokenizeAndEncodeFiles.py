#!/usr/bin/python
import os
import subprocess
import multiprocessing
import re


def noShellCall(arg):
    subprocess.call(arg, shell=False)


def shellCall(arg):
    subprocess.call(' '.join(arg), shell=True)


class bookidlist:
    def __init__(self):
        filelists = os.listdir('files/texts/textids')
        bookids = []
        for filename in filelists:
            for line in open('files/texts/textids/%s' % filename):
                splitted = line.split('\t')
                intid = splitted[0]
                bookid = splitted[1]
                bookid = bookid.replace('\n', '')
                bookid = bookid.replace(' ', '')
                bookids.append(bookid)
        self.bookids = bookids

        print "Done reading in files: moving to create subprocesses"
        self.processors = multiprocessing.cpu_count()
        #A ridiculous line of code to ensure that we don't have too little ram.
        try: # First try Ubuntu
            checkcpus = subprocess.Popen(['free', '-g'], stdout=subprocess.PIPE)
            gigsOfRam = int(re.findall('Mem: (.*) ', checkcpus.stdout.read())[0].strip().split(' ')[0])
        except OSError: # OS X will throw an OSError if the try above failed, so try an OS X command
            checkcpus = subprocess.Popen(['sysctl', 'hw.memsize'], stdout=subprocess.PIPE)
            gigsOfRam = int(checkcpus.stdout.read().strip().split(' ')[1])/1024**3
        except: #free doesn't exist on OS X; currently just doing it single-core.
            gigsOfRam = 1
        #Rule of thumb: each process needs to have a gig of memory, lest things get out of control
        self.simultaneousTasks = min([self.processors, gigsOfRam])
        
        #We can accept at most 100K arguments at a time on the command line.
        #but varies from system to system. So break up the chunks into lots and lots of pieces.
        #Processes is different than processors.
        self.processes = max([self.processors,int(len(self.bookids)/2000)])
        #and make it divisible by the number of processors which should help make it go optimally fast.
        #(although it should maybe be down to n-1 or something, in case one thread is hanging or one is super-speedy)
        self.processes = int(self.processes/self.processors)*self.processors + self.processors
        self.booklists = [bookids[i::self.processes] for i in range(self.processes)]

    def encode(self,mode):
        #mode is 'unigrams' or 'bigrams' (or trigrams)
        #This just takes the raw file, the perl script knows where to look.
        #Not the cleanest.
        self.args = [['perl', 'scripts/encodeText.pl', mode] + booklist for booklist in self.booklists]

    def createUnigramsAndBigrams(self):
        self.args = [['perl', 'scripts/makeUnigramsandBigrams.pl'] + booklist for booklist in self.booklists]
        self.execute()

    def encodeAll(self):
        self.args = [['perl', 'scripts/encodeAllTypes.pl'] + booklist for booklist in self.booklists]
        self.execute()
        

    def tokenize(self,mode):
        #Now obsoleted: code should be cleared out.
        if mode=='trigrams':
            n = 3
        if mode=='bigrams':
            n = 2
        if mode=='unigrams':
            n = 1
        if not mode in ('unigrams', 'bigrams', 'trigrams'):
            print "must specify mode of 'unigrams' or 'bigrams'" 
            raise
        self.args = []
        for bookid in self.bookids:
            bookinstance = book(bookid)
            bookinstance.ngrams(n)
            myArg = bookinstance.generateArgument()
            if len(myArg) > 0: #many cases this will return empty
                self.args.append(myArg)
        self.execute(exMethod=shellCall)
        print 'Done Tokenizing'

    def clean(self):
        self.args=[]
        for bookid in self.bookids:
            bookinstance = book(bookid)
            bookinstance.clean()
            myArg = bookinstance.generateArgument()
            if len(myArg) > 0: #many cases this will return empty
                self.args.append(myArg)
        self.execute(exMethod=shellCall)
        print 'Done cleaning'

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
        pool = multiprocessing.Pool(processes=self.simultaneousTasks)
        pool.map(exMethod, self.args)
        pool.close()


class book:
    #This class takes a bookid. The first call is the method to prep (encode2,onegrams, etc); it creates an attribute self.execute() which can then be called to write the next file in the chain.
    #Ideally these could be linked together more flexibly than they are here to do multiple operations on a book at once in memory.
    #The different operations are cast in terms of pipes, because the basic stemming and tokenizing scripts are written mostly in perl and awk, not python
    #They are easy enough to call from the command line. 
    def __init__(self,bookid):
        self.bookid = bookid
        self.coreloc = "%s.txt" % bookid
        
    def ngrams(self,n):
        #This generalizes writing an awk script to pull out gram counts
        #The join loop here prints a string like '$(i+0) " " $(i+1) " " $(i+2)' that gets the words in position i to i+2 plus two as a group for the thing to use.
        #At some point 'unigrams' and 'bigrams' should be deleted as methods, and only this should be used.
        self.start_operator = "cat"
        self.start = "files/texts/cleaned/" + self.coreloc
        self.function = """awk '{ for(i=1; i<=NF-""" +str(n-1)+ """; i++)
                        {count[""" + ' " " '.join(["$(i+" + str(j) + ")" for j in range(0,n)]) + """]++}
                        }
                        END{
                        for(i in count){print i, count[i]}}'"""
        destinations = {1:"unigrams",2:"bigrams",3:"trigrams",4:"quadgrams",5:"quintgrams"}
        self.destination = "files/texts/"+destinations[n] +"/" + self.coreloc
                 
    def clean(self):
        self.start_operator = "cat"
        self.start = "files/texts/raw/%s" % self.coreloc
        self.function = "perl scripts/CleanText.pl"
        self.destination = "files/texts/cleaned/%s" % self.coreloc
        #self.execute = self.shell_execute

    def generateArgument(self):
        if os.path.exists(self.destination):
            #print "No action. %s already exists." % self.destination
            return []
        if not os.path.exists(self.start):
            print "No action. %s does not exist." % self.start
            return []
        if os.path.getsize(self.start) < 10:
            print "No action. %s is too small." % self.start
            return []
        shell_operators = [self.start_operator, self.start, "|", self.function, ">", self.destination]
        return shell_operators

if __name__ == '__main__':
    #for debugging
    bookids = bookidlist()
