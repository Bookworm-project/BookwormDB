from __future__ import print_function
from __future__ import absolute_import
import sys
from .tokenizer import *

for row in sys.stdin:
    parts = row.split("\t",1)
    filename = parts[0]
    try:
        tokens = tokenizer(parts[1])
    except IndexError:
        logging.warning("Found no tab in the input for \n" + filename[:50] + "\n...skipping row")
        continue
    out= u" ".join(tokens.tokenize())
    print(out.encode("utf-8"))
