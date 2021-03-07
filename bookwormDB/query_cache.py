import pyarrow as pa
from pyarrow import feather
import pandas as pd
from pathlib import Path

import logging
import json
import hashlib
import random 

def hashcode(query: dict) -> str:
    return hashlib.sha1(json.dumps(query).encode("utf-8")).hexdigest()

class Query_Cache:
    # By default, use locally stored feather files. If that's bad, it Would
    # be pretty easy to split the class out into anything using an API 
    # that maps from cache[query_dictionary] -> pandas_frame.
    
    def __init__(self, location,
                max_entries = 256,
                max_length = 2**8,
                cold_storage = None):
        """
        location: where to keep some cached queries as parquet.
        max_entries: the max size of the cache.
        max_length: row length above which a query is never cached.
        cold_storage: Optional location of a second, read-only cache.
                      Feather files in this can be nested at any depth.
        """
        self.location = location
        self.max_entries = max_entries
        self.max_length = max_length
        self.precache = {}
        
        if not Path(location).exists():
            Path(location).mkdir(parents = True)
        assert Path(location).is_dir()
        if cold_storage is not None:
            for path in Path(cold_storage).glob("**/*.feather"):
                code = str(path.with_suffix("").name)
                self.precache[code] = path
        
    def filepath(self, query: dict) -> Path: 
        code = hashcode(query)
        if code in self.precache:
            return self.precache[code]
        return (Path(self.location) / code).with_suffix(".feather")
        
    def __getitem__(self, query: dict) -> pd.DataFrame:
        if hashcode(query) in self.precache:
            # First check any manual queries.
#            print(self.precache[hashcode(query)])
            return feather.read_feather(self.precache[hashcode(query)])
            
        p = self.filepath(query)
        table = feather.read_feather(p)
        p.touch() # Note access for LRU cache flushing.
        return table
        
    def __setitem__(self, query: dict, table: pd.DataFrame):
        if table.shape[0] > self.max_length:
            return
        if not self.max_length:
            # 0 or None are both reasonable here.
            return 
        path = self.filepath(query).open(mode="wb")
        feather.write_feather(table, path, compression = "zstd")
        
    def trim_cache(self):
        """
        Remove all cached feather files except the first
        few (defined by the max_entries parameter of the class.)
        """
        files = Path(self.location).glob("*.feather")
        all_of_em = []
        for file in files:
            all_of_em = [-1 * file.stat().st_mtime, file]
        all_of_em.sort()
        for extra in all_of_em[self.max_entries:]:
            try:
                extra.unlink()
            except:
                logging.error(f"Unable to unlink file {extra}; assuming another thread got it first, although that's pretty unlikely!")
