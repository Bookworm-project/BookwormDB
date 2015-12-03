import os
import subprocess
import sys
from tokenizer import *
import logging
import argparse

# This script reads in a unigrams file that must be formatted
# as "textid token count."

def main():
    path = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument('action', help="set to 'encode' or 'wordIds'")
    parser.add_argument('unigrams', type=argparse.FileType('r'), default=sys.stdin,
                        nargs='?',
                        help="Unigram feature file input. Defaults to sys.stdin")
    parser.add_argument('--log-level', '-l', default="warn", help="Logging level.")
    args = parser.parse_args()

    if args.log_level:
        numeric_level = getattr(logging, args.log_level.upper(), None)
        if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level,
                            format='%(asctime)s:%(levelname)s:%(message)s', datefmt="%d/%Y %H:%M:%S")

    if args.action == "wordIds":
        writeWordIDs(args.unigrams)
    elif args.action == "encode":
        logging.debug("Starting feature encoding process")
        encodePreTokenizedStream(args.unigrams,levels=["unigrams"])
        #encodePreTokenizedStream(args.bigrams),levels=["bigrams"])
    else:
        logging.error("Need to specify action as either 'wordIds' or 'encode'")


def writeWordIDs(featurefile, sep=None):
    """
    The wordids are counted directly from the unigrams file.

    Filename: location of unigrams.txt
    sep: Delimiter. Defaults to None (whitespace), use this for tab- or 
            comma-delimiting. 
    """
    
    output = open(".bookworm/texts/wordlist/wordlist.txt","w")
    wordcounts = dict()
    for line in featurefile:
        (bookid,word,count) = line.split(sep)
        count = int(count)
        try:
            wordcounts[word] += count
        except KeyError:
            wordcounts[word] = count
    tuples = [(v,k) for k,v in wordcounts.iteritems()]
    tuples.sort()
    tuples.reverse()
    wordid = 0
    for (count,word) in tuples:
        wordid += 1
        output.write("\t".join([str(wordid),word.replace("\\","\\\\"),str(count)]) + "\n")

if __name__ == '__main__':
    main()

