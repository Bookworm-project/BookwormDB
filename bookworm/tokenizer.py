#! /usr/bin/python

import regex as re
import cPickle as pickle
import random
import sys
import os 

def wordRegex():
    #I'm including the code to create the regex, which makes it more readable.
    MasterExpression = ur"\p{L}+"
    possessive = MasterExpression + ur"'s"
    numbers = "[\$?]\d+"
    decimals = "[\$?]\d+\.\d+"
    abbreviation = r"(?:mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\."
    sharps = r"[a-gjxA-GJX]#"
    punctuators = r"[^\p{L}\p{Z}]"
    """
    Note: this compiles looking for the most complicated words first, and as it goes on finds simpler and simpler forms 
    """
    bigregex = re.compile("|".join([decimals,possessive,numbers,abbreviation,sharps,punctuators,MasterExpression]),re.UNICODE|re.IGNORECASE)
    return bigregex

bigregex = wordRegex()

def readDictionaryFile():
    look = dict()
    for line in open("files/texts/wordlist/wordlist.txt"):
        line = line.rstrip("\n")
        splat = line.split("\t")
        look[splat[1]] = splat[0]
    return look

def readIDfile():
    files = os.listdir("files/texts/textids/")
    look = dict()
    for filename in files:
        for line in open("files/texts/textids/" + filename):
            line = line.rstrip("\n")
            splat = line.split("\t")
            look[splat[1]] = splat[0]
    return look

class tokenBatches(object):
    def __init__(self,levels=["unigrams","bigrams"]):
        self.counts = dict()
        self.counts["unigrams"] = dict()
        self.counts["bigrams"]  = dict()
        self.counts["trigrams"] = dict()
        self.id = '%030x' % random.randrange(16**30)
        self.levels=levels

    def addFile(self,filename):
        tokens = tokenizer(filename.readlines())
        #Add trigrams to this list to do trigrams
        for ngrams in self.levels:
            self.counts[ngrams][filename] = tokenizer.counts(ngrams)

    def addRow(self,row):
        #row is a piece of text: the first line is the identifier, and the rest is the text.
        parts = row.split("\t",1)
        filename = parts[0]
        tokens = tokenizer(parts[1])
        for ngrams in self.levels:
            self.counts[ngrams][filename] = tokens.counts(ngrams)

    def pickleMe(self):
        #Often we'll have to pickle, then create the word counts, then unpickle 
        #to build the database-loadable infrastructure
        outputFile = open("files/texts/unigrams/" + self.id,"w")
        pickle.dump(self,file=outputFile,protocol=-1)

    def encode(self,level,IDfile,dictionary):
        #dictionaryFile is
        outputFile = open("files/texts/encoded/" + level + "/" + self.id + ".txt","w")
        output = []
        for key,value in self.counts[level].iteritems():
            try:
                textid = IDfile[key]
            except KeyError:
                continue
            for wordset,count in value.iteritems():
                skip = False
                wordList = []
                for word in wordset:
                    try:
                        wordList.append(dictionary[word])
                    except KeyError:
                        """
                        if any of the words to be included is not in the dictionary,
                        we don't include the whole n-gram in the counts.
                        """
                        skip = True
            if not skip:
                wordids = "\t".join(wordList)
                output.append("\t".join([textid,wordids,str(count)]))
                
        outputFile.write("\n".join(output))        
     
    def unigramCounts(self,withDelete=False):
        if not "counts" in self.counts:
            self.counts["counts"] = dict()
        for documentNum in self.counts["unigrams"].keys():
            document = self.counts["unigrams"][documentNum]
            for key in document.keys():
                word = key[0]
                try:
                    self.counts["counts"][word] += document[key]
                except KeyError:
                    self.counts["counts"][word]  = document[key]
            if withDelete:
                del self.counts["unigrams"][documentNum]

    def writeUnigramCounts(self):
        print "joining up counts"
        outfile = open("files/texts/wordlist/raw-" + self.id + ".txt","w")
        output = []
        print self.counts.keys()
        counts =  self.counts["counts"]
        for word in counts:
            output.append(" ".join([word,str(counts[word])]))
        outfile.write("\n".join(output))

class tokenizer(object):
    def __init__(self,string):
        self.string=string

    def tokenize(self):
        try:
            return self.tokens
        except:
            #return bigregex
            self.tokens = re.findall(bigregex,self.string)
            return self.tokens

    def bigrams(self):
        self.tokenize()
        return zip(self.tokens,self.tokens[1:])

    def trigrams(self):
        self.tokenize()
        return zip(self.tokens,self.tokens[1:],self.tokens[2:])

    def unigrams(self):
        self.tokenize()
        #Note the comma to enforce tupleness
        return [(x,) for x in self.tokens]
    
    def counts(self,whichType):
        count = dict()
        for gram in getattr(self,whichType)():
            try:
                count[gram] += 1
            except KeyError:
                count[gram] = 1
        return count

def readTextStream():
    tokenBatch = tokenBatches()
    for line in sys.stdin:
        tokenBatch.addRow(line)
        
    return tokenBatch

def loadTextFiles():
    tokenBatch = tokenBatches()
    for filename in sys.argv:
        tokenBatch.addFile(filename)
    
def WordCounts():
    tokenBatch = tokenBatches(levels=["unigrams"])
    i = 1
    for line in sys.stdin:
        i += 1
        if i % 1000 == 0:
            print str(i)
        tokenBatch.addRow(line)
        tokenBatch.unigramCounts(withDelete=True)
    tokenBatch.writeUnigramCounts()

if __name__=="__main__":
    WordCounts()
    #tokenBatch = readTextStream()
