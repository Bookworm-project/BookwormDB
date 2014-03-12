#! /usr/bin/python

import regex as re
import cPickle as pickle
import random
import sys

def BigRegex():
    #I'm including the code to create the regex, which makes it more readable.
    MasterExpression = ur"\p{L}+"
    possessive = MasterExpression + ur"'s"
    numbers = "[\$?]\d+"
    decimals = "[\$?]\d+\.\d+"
    abbreviation = r"(?:mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\."
    sharps = r"[a-gjxA-GJX]#"
    punctuators = r"[^\p{L}\p{Z}]"

    bigregex = re.compile("|".join([possessive,numbers,abbreviation,sharps,punctuators,MasterExpression]),re.UNICODE|re.IGNORECASE)
    return bigregex

def readDictionaryFile():
    pass

def readIDfile():
    pass

class tokenBatches(object):
    def __init__(self,levels=["unigrams","bigrams"]):
        self.counts = dict()
        self.counts["unigrams"] = dict()
        self.counts["bigrams"]  = dict()
        self.counts["trigrams"] = dict()
        self.id =  '%030x' % random.randrange(16**30)


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
            self.counts[ngrams][filename] = tokenizer.counts(ngrams)

    def pickleMe(self):
        #Often we'll have to pickle, then create the word counts, then unpickle 
        #to build the database-loadable infrastructure
        outputFile = "files/texts/wordcounts/" + self.id
        pickle.dump(self,file=outputFile,protocol="HIGHEST_PROTOCOL")

    def encode(self,dictionaryFile,IDfile,level):

        #dictionaryFile is
        outputFile = open("files/texts/encoded/" + level + "/" + self.id + ".txt","w")
        IDfile = readIDfile(IDfile)
        dictionary = readDictionaryFile(dictionary)
        output = []
        for key,value in self.counts[level].iteritems():
            textid = IDfile[key]
            for wordset,count in value.iteritems():
                wordids = "\t".join[dictionary[word] for word in wordset] 
                output.append("\t".join([textid,wordids,str(count)]))
                
        outputFile.write("\n".join(output))        
     
    def unigramCounts(self):
        counts = dict()
        for document in self.counts["unigrams"]:
            for key in document.keys():
                word = key[0]
                try:
                    counts[word] += 1
                except KeyError:
                    pass

class tokenizer(object):
    def __init__(self,string):
        self.string=string

    def tokenize(self):
        try:
            return self.tokens
        except:
            bigregex = BigRegex()
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
    for line in sys.stdin():
        tokenBatch.addRow(line)
        
    return tokenBatch

def loadTextFiles():
    tokenBatch = tokenBatches()
    for filename in sys.argv:
        tokenBatch.addFile(filename)
    

if __name__=="__main__":
    tokenBatch = readTextStream()
    tokenBatch.pickleMe()
        
