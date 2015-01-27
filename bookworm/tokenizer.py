#! /usr/bin/python

import regex as re
import random
import sys
import os
import anydbm

def wordRegex():
    """
    #I'm including the code to create the regex, which makes it more readable.
    Note that this uses *unicode*: among other things, that means that it needs to be passed
    a unicode-decoded string: and that we have to use the "regex" module instead of the "re" module. Python3 will make this, perhaps, easier.
    (See how it says import regex as re up there? Yikes.)
    """
    MasterExpression = ur"\p{L}+"
    possessive = MasterExpression + ur"'s"
    numbers = r"(?:[\$])?\d+"
    decimals = numbers + r"\.\d+"
    abbreviation = r"(?:mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\."
    sharps = r"[a-gjxA-GJX]#"
    punctuators = r"[^\p{L}\p{Z}]"
    """
    Note: this compiles looking for the most complicated words first, and as it goes on finds simpler and simpler forms 
    """
    bigregex = re.compile("|".join([decimals,possessive,numbers,abbreviation,sharps,punctuators,MasterExpression]),re.UNICODE|re.IGNORECASE)
    return bigregex

bigregex = wordRegex()

def readDictionaryFile(prefix=""):
    look = dict()
    for line in open(prefix + "files/texts/wordlist/wordlist.txt"):
        line = line.rstrip("\n")
        splat = line.split("\t")
        look[splat[1]] = splat[0]
    return look

def readIDfile(prefix=""):
    return anydbm.open(prefix + "files/texts/textids.dbm")

class tokenBatches(object):
    """
    A tokenBatches is a manager for tokenizers. Each one corresponds to 
    a reasonable number of texts to read in to memory on a single processor:
    during the initial loads, there will probably be one per core. It doesn't store the original text, just the unigram and bigram tokenizations from the pickled object in its attached self.counts arrays.
    
    It writes out its data using cPickle to a single file: in this way, a batch of several hundred thousand individual files is grouped into a single file.
    It also has a method that encodes and writes its wordcounts into a tsv file appropriate for reading with mysql, with 3-byte integer encoding for wordid and bookid.

    The pickle writeout happens in between so that there's a chance to build up a vocabular using the tokenBatches.unigramCounts method. If the vocabulary were preset, it could proceed straight to writing out the encoded results.

    The pickle might be slower than simply using a fast csv module: this should eventually be investigated. But it's nice for the pickled version to just keep all the original methods.
    """
    
    def __init__(self,levels=["unigrams","bigrams"]):
        self.id = '%030x' % random.randrange(16**30)
        self.levels=levels

        self.completedFile = open("files/texts/encoded/completed/" + self.id,"w")
        self.outputFiles = dict()
        for level in levels:
            self.outputFiles[level] = open("files/texts/encoded/" + level + "/" + self.id + ".txt","w")
    
    def attachDictionaryAndID(self):
        self.dictionary = readDictionaryFile()
        self.IDfile = readIDfile()

    def encodeRow(self,
                  row,
                  source="raw_text" # Can also be "countfile", in which case each row is a tab separated list of [filename,ngram,count], where ngrams can contain spaces.
    ):

        #The dictionary and ID lookup tables should be pre-attached.
        dictionary = self.dictionary
        IDfile = self.IDfile
            
        if source=="raw_text":
            parts = row.split("\t",1)
            filename = parts[0]
            try:
                tokens = tokenizer(parts[1])
            except IndexError:
                sys.stderr.write("\nFound no tab in the input for '" + filename + "'...skipping row\n")
            
        if source=="countfile":
            try:
                (filename,token,count) = row.split("\t")
            except:
                print row
                raise
            tokens = preTokenized(token,count,self.levels[0])

        try:
            textid = IDfile[filename]
        except KeyError:
            try:
                sys.stderr.write("Warning: file " + filename + " not found in jsoncatalog.txt, not encoding\n")
            except:
                "something went wrong"
            return



        for level in self.levels:
            outputFile = self.outputFiles[level]
            output = []

            counts = tokens.counts(level)

            for wordset,count in counts.iteritems():
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

            outputFile.write("\n".join(output) + "\n")        
        self.completedFile.write(filename + "\n")

haveWarnedUnicode = False

class tokenizer(object):
    """
    A tokenizer is initialized with a single text string.

    It assumes that you have in namespace an object called "bigregex" which
    identifies words.

    (I'd define it here, but it's a performance optimization to avoid compiling the large regex millions of times.)

    the general way to call it is to initialize, and then for each desired set of counts call "tokenizer.counts("bigrams")" (or whatever).

    That returns a dictionary, whose keys are tuples of length 1 for unigrams, 2 for bigrams, etc., and whose values are counts for that ngram. The tuple form should allow faster parsing down the road.
    
    """
    
    def __init__(self,string):
        global haveWarnedUnicode
        try:
            self.string = string.decode("UTF-8")
        except:
            if not haveWarnedUnicode:
                sys.stderr.write("WARNING: some of your input files seem not to be valid unicode. Silently ignoring all non-unicode characters from now on in this thread.\n")
                haveWarnedUnicode = True
            self.string = string.decode("UTF-8","ignore")

    def tokenize(self):
        """
        This tries to return the pre-made tokenization:
        if that doesn't exist, it creates it.
        """
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


class preTokenized(object):
    """
    This class is a little goofy: it mimics the behavior of a tokenizer
    one data that's already been tokenized by something like 
    Google Ngrams or JStor Data for Research.
    """

    def __init__(self,token,count,level):
        self.level = level
        self.output = {tuple(token.split(" ")):count}
        
    def counts(self,level):
        if level!= self.level:
            raise
        return self.output
    
    
def getAlreadySeenList(folder):
    #Load in a list of what's already been translated for that level.
    #Returns a set.
    files = os.listdir(folder)
    seen = set([])
    for file in files:
        for line in open(folder+"/" + file):
            seen.add(line.rstrip("\n"))
    return seen

def encodeTextStream():
    seen = getAlreadySeenList("files/texts/encoded/completed")
    tokenBatch = tokenBatches()
    tokenBatch.attachDictionaryAndID()
    for line in sys.stdin:
        filename = line.split("\t",1)[0]
        line = line.rstrip("\n")
        if filename not in seen:
            tokenBatch.encodeRow(line)
            
    #And printout again at the end

def encodePreTokenizedStream(file,levels=["unigrams"]):
    """
    Note: since unigrams and bigrams are done separately, we have to just redo the whole
    thing every time. The prebuilt list don't work.
    """
    seen = getAlreadySeenList("files/texts/encoded/completed")
    tokenBatch = tokenBatches(levels=levels)
    tokenBatch.attachDictionaryAndID()
    for line in file:
        filename = line.split("\t",1)[0]
        line = line.rstrip("\n")
        if filename not in seen:
            tokenBatch.encodeRow(line,source="countfile")

    
if __name__=="__main__":
    encodeTextStream()
