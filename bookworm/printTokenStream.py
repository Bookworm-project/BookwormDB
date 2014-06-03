import sys
from tokenizer import *
import warnings

for row in sys.stdin:
    parts = row.split("\t",1)
    filename = parts[0]
    try:
        tokens = tokenizer(parts[1])
    except IndexError:
        warn("Found no tab in the input for \n" + filename[:50] + "\n...skipping row")
        continue
    out= u" ".join(tokens.tokenize())
    print out.encode("utf-8")
