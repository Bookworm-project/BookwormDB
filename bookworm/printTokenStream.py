import sys
from tokenizer import *

for row in sys.stdin:
    parts = row.split("\t",1)
    filename = parts[0]
    try:
        tokens = tokenizer(parts[1])
    except IndexError:
        print "Found no tab in the input for \n" + filename + "\n...skipping row"
        continue
    for token in tokens.tokenize():
        print token
