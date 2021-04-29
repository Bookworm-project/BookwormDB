# Just a place to store per-process configurations rather than pass through a 
# nest of functions. Bad idea? Probably--I got it from too much Javascript.
# Only one location should ever have write
# access, certainly. But this should be easier to disentangle than endless passed 'args.whatever'

import yaml
from pathlib import Path 

store_dict = {
    'duckdb_directory': Path(".")
}

directories =  [Path("."), Path("/var/lib/bookworm/"), *Path(".").parents, Path("~").expanduser()]
directories.reverse() # because we want the immediate parent first.

for dir in directories:
    for file in [".bookworm.yaml", ".bookworm.yml", "bookworm.yaml"]:
        p = dir / file
        if p.exists():
            print("Loading", dir)
            store_dict = yaml.safe_load(p.open())

def store():
    global store_dict
    return store_dict

