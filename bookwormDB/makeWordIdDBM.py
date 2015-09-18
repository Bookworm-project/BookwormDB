#/usr/bin/python

"""
This quickly creates a key-value store for textids: storing on disk
dramatically reduces memory consumption for bookworms of over 
1 million documents.
"""

import anydbm
import os

def text_id_dbm():
    dbm = anydbm.open(".bookworm/texts/textids.dbm","c")
    for file in os.listdir(".bookworm/texts/textids"):
        for line in open(".bookworm/texts/textids/" + file):        
            line = line.rstrip("\n")
            splat = line.split("\t")
            dbm[splat[1]] = splat[0]

if __name__=="__main__":
    text_id_dbm()
